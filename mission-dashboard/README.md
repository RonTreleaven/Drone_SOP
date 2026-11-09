# Drone_SOP Mission Planner

This is the GitHub Pages edition of the Canadian RPAS mission dashboard. It is
linked under **Tools → Flight Planning** and builds into `dist/` with Node 24.

```sh
npm ci
npm run build
```

The dashboard reads KML in the browser. Selecting **Fetch forecast** sends the
selected coordinates to Open-Meteo. The Pages edition saves mission records
in the current browser. The evidence report can be downloaded as a text file.

The route schematic displays imported geometry. Use the linked official
sources to review airspace, NOTAMs and applicable restrictions independently.
