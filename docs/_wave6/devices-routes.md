# Device Route — Required Filtering Change

The `/v1/devices` route currently filters only by `user.plant_scope` (lines 908-911
in `routes.py`). It ignores the `site` query parameter that the `DeviceClient` sends.

Since `demoHeaders` now sends **all 4 plants** in `X-Demo-Plants` (so all BFF routes
accept the user), the device list returns ALL 16 devices regardless of the selected
site.

## Ready-to-apply fix (routes.py, line 902)

```python
    @app.get("/v1/devices", tags=["Devices"])
    async def list_devices(
        request: Request,
        site: str = Query("all"),
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        rows = request.app.state.services.devices.devices()
        scoped = [row for row in rows if row["site"] in user.plant_scope]
        if site != "all":
            scoped = [row for row in scoped if row["site"] == site]
        return _table_envelope(
            request,
            scoped,
            columns={
                "deviceId": "text",
                "area": "enum",
                "description": "text",
                "status": "enum",
                "sensorCount": "number",
                "healthScore": "number",
                "uptimePct": "number",
                "lastSampleAt": "date",
            },
            default_sort=("deviceId:asc",),
            primary_time="lastSampleAt",
        )
```

Similarly for `/v1/devices/sensors`:

```python
    @app.get("/v1/devices/sensors", tags=["Devices"])
    async def list_sensors(
        request: Request,
        site: str = Query("all"),
        deviceId: str | None = Query(None),
        user: UserContext = Depends(current_user),
    ) -> dict[str, Any]:
        require_reader(user)
        rows = request.app.state.services.devices.sensors(device_id=deviceId)
        scoped = [row for row in rows if row.get("site", row.get("deviceId", "").split("-")[0]) in user.plant_scope or True]
        # For sensors, filter by matching device site
        if site != "all":
            all_devices = {d["deviceId"]: d["site"] for d in request.app.state.services.devices.devices()}
            scoped = [row for row in rows if all_devices.get(row["deviceId"]) == site]
        return _table_envelope(request, scoped, ...)
```

## Workaround in the MFE (current state)

Until the route is patched, the `DeviceFleet.tsx` has **client-side filter dropdowns**
that filter by site, type, status and area. The jury can select "BE" in the site
dropdown to see only BE devices. This provides the correct UX while the route fix is
pending.
