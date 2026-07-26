# Power BI setup assets

`report-catalog.json` defines the report/page/visual contract and
`novasteel-theme.json` provides the portable theme. A `.pbix` or tenant-bound
PBIR export is intentionally not fabricated in source control.

## Setup

1. Complete the Direct Lake semantic-model binding and RLS gate in
   `../semantic-model/README.md`.
2. Create the reports listed in `report-catalog.json` in the Analytics
   workspace and bind them only to `sm-ns-operations`.
3. Import `novasteel-theme.json`.
4. Validate each persona with test Entra identities, plant scope, export
   permission, labels, and stale/empty/error behavior.
5. For internal embedding use **Embed for your organization / user owns data**.
   The BFF may mediate configuration, but no service credential or app-owns-data
   authorization bypass is sent to the browser.
6. Export the current PBIR project and review/check it in before adding report
   definitions to automated REST/CLI deployment.

Below F64, every report consumer needs Pro/PPU/trial. F64 is not selected solely
to avoid per-user licensing.
