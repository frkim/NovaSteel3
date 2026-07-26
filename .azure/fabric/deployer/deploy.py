import base64
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


ROOT = Path("/opt/novasteel-fabric")
FABRIC_ROOT = ROOT / "fabric"
PARAMETER_PATH = FABRIC_ROOT / "deployment-parameters" / "novasteelv3.parameters.json"
MANIFEST_PATH = FABRIC_ROOT / "deployment-parameters" / "novasteelv3.items-manifest.json"
FABRIC_API = "https://api.fabric.microsoft.com/v1"
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


def managed_identity_token(resource):
    endpoint = os.environ["IDENTITY_ENDPOINT"]
    header = os.environ["IDENTITY_HEADER"]
    query = urllib.parse.urlencode(
        {
            "resource": resource,
            "api-version": "2019-08-01",
            "client_id": os.environ["AZURE_CLIENT_ID"],
        }
    )
    request = urllib.request.Request(
        f"{endpoint}?{query}",
        headers={"X-IDENTITY-HEADER": header},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)["access_token"]


def http(method, url, token, body=None, max_retries=6):
    encoded = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if body is not None:
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    for attempt in range(1, max_retries + 1):
        request = urllib.request.Request(
            url,
            data=encoded,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                content = response.read().decode("utf-8")
                payload = json.loads(content) if content else None
                return response.status, dict(response.headers), payload
        except urllib.error.HTTPError as error:
            content = error.read().decode("utf-8", errors="replace")
            if error.code in RETRYABLE_STATUS and attempt < max_retries:
                retry_after = error.headers.get("Retry-After")
                delay = int(retry_after) if retry_after and retry_after.isdigit() else min(60, 2**attempt)
                time.sleep(delay)
                continue
            raise RuntimeError(f"HTTP {error.code}: {method} {url}\n{content}") from error
        except urllib.error.URLError as error:
            if attempt == max_retries:
                raise RuntimeError(f"Network failure: {method} {url}: {error}") from error
            time.sleep(min(60, 2**attempt))
    raise RuntimeError(f"HTTP retry loop exhausted: {method} {url}")


def header_value(headers, name):
    for key, value in headers.items():
        if key.lower() == name.lower():
            return value
    return None


def wait_operation(initial, token, timeout_seconds=1800):
    status, headers, payload = initial
    if status != 202:
        return payload

    operation_url = (
        header_value(headers, "Location")
        or header_value(headers, "Azure-AsyncOperation")
    )
    if not operation_url:
        operation_id = header_value(headers, "x-ms-operation-id")
        if operation_id:
            operation_url = f"{FABRIC_API}/operations/{operation_id}"
    if not operation_url:
        raise RuntimeError("Fabric returned 202 without an operation URL.")
    if operation_url.startswith("/"):
        operation_url = f"https://api.fabric.microsoft.com{operation_url}"

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        retry_after = header_value(headers, "Retry-After")
        delay = int(retry_after) if retry_after and str(retry_after).isdigit() else 5
        time.sleep(max(1, min(60, delay)))
        status, headers, payload = http("GET", operation_url, token)
        if payload is None:
            if status == 200:
                return None
            continue
        operation_status = str(payload.get("status") or payload.get("state") or "")
        if operation_status in {"Succeeded", "Completed", "Success"}:
            return payload
        if operation_status in {"Failed", "Cancelled", "Canceled"}:
            raise RuntimeError(f"Fabric operation failed: {json.dumps(payload)}")
        if not operation_status and status == 200:
            return payload
    raise RuntimeError(f"Fabric operation timed out: {operation_url}")


def fabric_request(method, path, token, body=None):
    url = path if path.startswith("http") else f"{FABRIC_API}{path}"
    response = http(method, url, token, body)
    return wait_operation(response, token)


def collection(path, token):
    values = []
    next_url = f"{FABRIC_API}{path}"
    while next_url:
        _, _, payload = http("GET", next_url, token)
        if payload is None:
            break
        if "value" in payload:
            values.extend(payload["value"])
        else:
            values.append(payload)
        next_url = payload.get("continuationUri")
        if not next_url and payload.get("continuationToken"):
            separator = "&" if "?" in path else "?"
            continuation = urllib.parse.quote(payload["continuationToken"], safe="")
            next_url = f"{FABRIC_API}{path}{separator}continuationToken={continuation}"
    return values


def exactly_one(items, display_name, item_type=None):
    matches = [
        item
        for item in items
        if item.get("displayName", "").casefold() == display_name.casefold()
        and (item_type is None or item.get("type", "").casefold() == item_type.casefold())
    ]
    if len(matches) > 1:
        raise RuntimeError(f"More than one matching Fabric object is named '{display_name}'.")
    return matches[0] if matches else None


def ensure_workspace_access(workspace_id, token):
    principal_id = os.environ.get("FABRIC_ACCESS_PRINCIPAL_ID", "").strip()
    if not principal_id:
        return None

    try:
        uuid.UUID(principal_id)
    except ValueError as error:
        raise RuntimeError("FABRIC_ACCESS_PRINCIPAL_ID must be a UUID.") from error

    principal_type = os.environ.get("FABRIC_ACCESS_PRINCIPAL_TYPE", "User").strip()
    if principal_type not in {"User", "ServicePrincipal", "Group"}:
        raise RuntimeError(
            "FABRIC_ACCESS_PRINCIPAL_TYPE must be User, ServicePrincipal, or Group."
        )

    role = os.environ.get("FABRIC_ACCESS_ROLE", "Admin").strip()
    if role not in {"Admin", "Member", "Contributor", "Viewer"}:
        raise RuntimeError(
            "FABRIC_ACCESS_ROLE must be Admin, Member, Contributor, or Viewer."
        )

    path = f"/workspaces/{workspace_id}/roleAssignments"
    assignments = collection(path, token)
    assignment = next(
        (
            item
            for item in assignments
            if item.get("principal", {}).get("id") == principal_id
        ),
        None,
    )
    if assignment is None:
        fabric_request(
            "POST",
            path,
            token,
            {
                "principal": {"id": principal_id, "type": principal_type},
                "role": role,
            },
        )
        action = "created"
    elif assignment.get("role") != role:
        fabric_request(
            "PATCH",
            f"{path}/{assignment['id']}",
            token,
            {"role": role},
        )
        action = "updated"
    else:
        action = "unchanged"

    verified = next(
        (
            item
            for item in collection(path, token)
            if item.get("principal", {}).get("id") == principal_id
        ),
        None,
    )
    if verified is None or verified.get("role") != role:
        raise RuntimeError("Fabric workspace role assignment verification failed.")

    result = {
        "action": action,
        "workspaceId": workspace_id,
        "principalId": principal_id,
        "principalType": principal_type,
        "role": role,
        "displayName": verified.get("principal", {}).get("displayName"),
        "userPrincipalName": (
            verified.get("principal", {})
            .get("userDetails", {})
            .get("userPrincipalName")
        ),
    }
    print(f"FABRIC_WORKSPACE_ACCESS={json.dumps(result, separators=(',', ':'))}", flush=True)
    return result


def wait_for_item(workspace_id, display_name, item_type, token):
    for _ in range(60):
        item = exactly_one(
            collection(f"/workspaces/{workspace_id}/items", token),
            display_name,
            item_type,
        )
        if item:
            return item
        time.sleep(5)
    raise RuntimeError(f"Fabric item was not found after deployment: {item_type}/{display_name}")


def replacement_map(parameters, workspace_id, workspace_name, state_items):
    replacements = {
        "{{environment}}": parameters["environment"],
        "{{workspace.id}}": workspace_id,
        "{{workspace.displayName}}": workspace_name,
        "{{workspace.rtiIngress.id}}": workspace_id,
        "{{workspace.dataCore.id}}": workspace_id,
        "{{workspace.ml.id}}": workspace_id,
    }
    for key, item in state_items.items():
        replacements[f"{{{{item.{key}.id}}}}"] = item["id"]
        replacements[f"{{{{item.{key}.displayName}}}}"] = item["displayName"]
    for key, value in parameters["retention"].items():
        replacements[f"{{{{retention.{key}}}}}"] = value

    landing = parameters["onelake"]["landingTablesUri"]
    if "<" in landing and "landingLakehouse" in state_items:
        landing = (
            f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/"
            f"{state_items['landingLakehouse']['id']}/Tables"
        )
    core = parameters["onelake"]["coreTablesUri"]
    if "<" in core and "coreLakehouse" in state_items:
        core = (
            f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/"
            f"{state_items['coreLakehouse']['id']}/Tables"
        )
    replacements["{{onelake.landingTablesUri}}"] = landing
    replacements["{{onelake.coreTablesUri}}"] = core
    return replacements


def definition_for(spec, replacements):
    parts = []
    source = FABRIC_ROOT / spec["sourceDirectory"]
    for relative_path in spec["definitionParts"]:
        path = source / relative_path
        content = path.read_text(encoding="utf-8")
        for key in sorted(replacements, key=len, reverse=True):
            content = content.replace(key, replacements[key])
        unresolved = sorted(set(re.findall(r"\{\{[^{}]+\}\}", content)))
        if unresolved:
            raise RuntimeError(f"Unresolved tokens in {path}: {', '.join(unresolved)}")
        parts.append(
            {
                "path": relative_path.replace("\\", "/"),
                "payload": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "payloadType": "InlineBase64",
            }
        )
    definition = {"parts": parts}
    if spec.get("definitionFormat"):
        definition["format"] = spec["definitionFormat"]
    return definition


def main():
    parameters = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    token = managed_identity_token("https://api.fabric.microsoft.com")

    capacity = exactly_one(
        collection("/capacities", token),
        parameters["capacity"]["name"],
    )
    if not capacity:
        raise RuntimeError(
            f"Managed identity cannot see Fabric capacity '{parameters['capacity']['name']}'."
        )
    capacity_id = capacity["id"]
    print(f"FABRIC_CAPACITY_ID={capacity_id}", flush=True)

    workspace_name = parameters["workspace"]["displayName"]
    workspace = exactly_one(collection("/workspaces", token), workspace_name)
    if not workspace:
        body = {
            "displayName": workspace_name,
            "description": (
                "Isolated synthetic-only novasteelv3 demo workspace. "
                "Never used by the existing NovaSteel estate."
            ),
            "capacityId": capacity_id,
        }
        fabric_request("POST", "/workspaces", token, body)
        for _ in range(60):
            workspace = exactly_one(collection("/workspaces", token), workspace_name)
            if workspace:
                break
            time.sleep(5)
    if not workspace:
        raise RuntimeError(f"Workspace '{workspace_name}' was not found after creation.")

    workspace_id = workspace["id"]
    if workspace.get("capacityId") != capacity_id:
        fabric_request(
            "POST",
            f"/workspaces/{workspace_id}/assignToCapacity",
            token,
            {"capacityId": capacity_id},
        )

    workspace_access = ensure_workspace_access(workspace_id, token)
    if os.environ.get("FABRIC_ACCESS_ONLY", "").strip().lower() == "true":
        if workspace_access is None:
            raise RuntimeError(
                "FABRIC_ACCESS_ONLY requires FABRIC_ACCESS_PRINCIPAL_ID."
            )
        print(json.dumps({"workspaceAccess": workspace_access}, indent=2), flush=True)
        return

    state_items = {}
    for spec in manifest["supportedItems"]:
        option = spec["deploymentOption"]
        if not parameters["deploymentOptions"].get(option, True):
            print(f"SKIP {spec['key']}: {option}=false", flush=True)
            continue
        gate = spec.get("bindingGate")
        if gate and not parameters["deploymentOptions"].get(gate, False):
            print(f"GATE {spec['key']}: {gate}=false", flush=True)
            continue
        for dependency in spec["dependencies"]:
            if dependency not in state_items:
                raise RuntimeError(f"{spec['key']} depends on undeployed item {dependency}.")

        key = spec["key"]
        item_config = parameters["items"].get(key, {})
        display_name = item_config.get("displayName") or spec["displayName"]
        existing = exactly_one(
            collection(f"/workspaces/{workspace_id}/items", token),
            display_name,
            spec["type"],
        )
        definition = None
        if not spec["createWithoutDefinition"]:
            definition = definition_for(
                spec,
                replacement_map(parameters, workspace_id, workspace_name, state_items),
            )

        if existing is None:
            body = {
                "displayName": display_name,
                "description": spec["description"],
            }
            if definition is not None:
                body["definition"] = definition
            fabric_request(
                "POST",
                f"/workspaces/{workspace_id}{spec['restCollection']}",
                token,
                body,
            )
        elif definition is not None:
            fabric_request(
                "POST",
                f"/workspaces/{workspace_id}/items/{existing['id']}/updateDefinition?updateMetadata=true",
                token,
                {"definition": definition},
            )

        resolved = wait_for_item(workspace_id, display_name, spec["type"], token)
        state_items[key] = {
            "id": resolved["id"],
            "displayName": display_name,
            "type": spec["type"],
        }
        print(f"READY {key}: {resolved['id']}", flush=True)

    state = {
        "schemaVersion": 1,
        "project": "novasteelv3",
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "capacity": {
            "id": capacity_id,
            "displayName": parameters["capacity"]["name"],
            "state": capacity.get("state"),
        },
        "workspace": {
            "id": workspace_id,
            "displayName": workspace_name,
            "capacityId": capacity_id,
        },
        "items": state_items,
        "manualGates": [
            {"key": item["key"], "reason": item["reason"]}
            for item in manifest["excludedItems"] + manifest["manualAssets"]
        ],
    }
    encoded_state = base64.b64encode(
        json.dumps(state, separators=(",", ":")).encode("utf-8")
    ).decode("ascii")
    print(f"NOVASTEEL_FABRIC_STATE_BASE64={encoded_state}", flush=True)
    print(json.dumps(state, indent=2), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"NOVASTEEL_DEPLOY_ERROR={error}", flush=True)
        raise
