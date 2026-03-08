<-- app.js function to checkWeather for wind risk 



async function checkWeather() {

  const icao = document.getElementById("icao").value.toUpperCase();
  const output = document.getElementById("output");

  const url = `https://aviationweather.gov/api/data/metar?ids=${icao}&format=json`;

  try {

    const response = await fetch(url);
    const data = await response.json();

    if (!data.length) {
      output.textContent = "No METAR found.";
      return;
    }

    const metar = data[0];

    const wind = metar.wspd || 0;
    const gust = metar.wgst || wind;
    const vis = metar.visib || 10;
    const ceiling = metar.ceil || 5000;

    const score = droneRisk(wind, gust, vis, ceiling);

    output.textContent =
`METAR: ${metar.rawOb}

Wind: ${wind} kt
Gust: ${gust} kt
Visibility: ${vis} SM
Ceiling: ${ceiling} ft

Risk Score: ${score}
${riskLabel(score)}
`;

  } catch (err) {
    output.textContent = "Error fetching weather.";
  }
}