# Gold v2 Notam Builder.py & NotamsMap.html dox.

March 9, 2026

Multimap source selectors introduced.... toggle by map layer

Done. 

All requested UI updates are now implemented in `Gold v2 Notam Map Builder.py` and confirmed in generated output.

### What changed

1. Layers selector icon + label for map basemaps

- Added a dedicated basemap control class: [map-layers-control](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- Replaced default layers icon with a compass-style Font Awesome icon.
- Added tooltip/ARIA label: [Map Layers](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html).

1. Separate Obstacles/Airports selector icon + label

- Added a separate overlay control class: [airports-obstacles-control](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- Label now shows: `Airports & Obstacles`.
- Added custom icon for that control.

1. Overlay label renamed

- Overlay layer displayed as:
  - `Airports & Obstacles`

1. Center Map icon control

- Added a top-left target/crosshairs button (`fa-crosshairs`) that recenters map to pilot position at current zoom any time.
- Includes tooltip/ARIA: `Center Map on Pilot`.

### Where in code

- Styling for new control icons/buttons: `Gold v2 Notam Map Builder.py:420`
- New basemap + overlay control setup and labels: `Gold v2 Notam Map Builder.py:462`
- New center-map control/button: `Gold v2 Notam Map Builder.py:845`

### Output verified

Generated [NotamsMap_controls_test.html](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html) contains:

- [map-layers-control](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- [airports-obstacles-control](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- `Airports & Obstacles`
- [Map Layers](vscode-file://vscode-app/c:/Users/Ron Treleaven/AppData/Local/Programs/Microsoft VS Code/61b3d0ab13/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
- center-map control with `fa-crosshairs`