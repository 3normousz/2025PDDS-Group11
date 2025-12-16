const width = 750;
const height = 500;

const svg = d3
  .select("#worldHeatmap")
  .append("svg")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", `0 0 ${width} ${height}`)
  .attr("preserveAspectRatio", "xMidYMid meet")
  .style("width", "100%")
  .style("height", "100%");

const g = svg.append("g");

// Zoom behavior
const zoom = d3
  .zoom()
  .scaleExtent([1, 8])
  .on("zoom", (event) => {
    g.attr("transform", event.transform);
  });

svg.call(zoom);

const projection = d3
  .geoNaturalEarth1()
  .scale(150)
  .translate([width / 2 - 50, height / 2]);

const path = d3.geoPath().projection(projection);

const colorScale = d3
  .scaleLinear()
  .domain([0, 15, 30, 50])
  .range(["#fdeff9", "#ec38bc", "#7303c0", "#0a015b"])
  .clamp(true);

const tooltip = d3.select("#tooltip");

Promise.all([
  d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"),
  fetch("/api/world-heatmap").then((res) => res.json()),
])
  .then(([topology, violenceData]) => {
    const countries = topojson.feature(topology, topology.objects.countries);

    // Get max value for color scale
    const rawMaxValue = Math.max(...Object.values(violenceData));
    const minValue = Math.min(...Object.values(violenceData));

    // Round up to nearest 10
    const maxValue = Math.ceil(rawMaxValue / 10) * 10;

    // Update color scale domain dynamically
    colorScale.domain([
      minValue,
      minValue + (maxValue - minValue) * 0.33,
      minValue + (maxValue - minValue) * 0.66,
      maxValue,
    ]);

    // d3.select("#maxValue").text(`${maxValue}%`);

    // Create a mapping from country names to ISO codes
    const countryNameToId = {
      "United States": "840",
      "United Kingdom": "826",
      France: "250",
      Germany: "276",
      Italy: "380",
      Spain: "724",
      China: "156",
      India: "356",
      Brazil: "076",
      Russia: "643",
      Canada: "124",
      Australia: "036",
      Japan: "392",
      Mexico: "484",
      "South Africa": "710",
      Egypt: "818",
      Nigeria: "566",
      Kenya: "404",
      Tanzania: "834",
      Uganda: "800",
      Ethiopia: "231",
      Ghana: "288",
      Mali: "466",
      Senegal: "686",
      Mozambique: "508",
      Zambia: "894",
      Zimbabwe: "716",
      Malawi: "454",
      Bangladesh: "050",
      Pakistan: "586",
      Philippines: "608",
      Indonesia: "360",
      Thailand: "764",
      Vietnam: "704",
      Turkey: "792",
      Argentina: "032",
      Colombia: "170",
      Peru: "604",
      Chile: "152",
      Ecuador: "218",
      Bolivia: "068",
      Guatemala: "320",
      Honduras: "340",
      Nicaragua: "558",
      Haiti: "332",
      "Dominican Republic": "214",
      Jordan: "400",
      Yemen: "887",
      Afghanistan: "004",
      Iraq: "368",
      Lebanon: "422",
      Morocco: "504",
      Algeria: "012",
      Tunisia: "788",
      Liberia: "430",
      "Sierra Leone": "694",
      Nepal: "524",
      Cambodia: "116",
      Myanmar: "104",
      "Kyrgyz Republic": "417",
      Tajikistan: "762",
      Armenia: "051",
      Azerbaijan: "031",
      Moldova: "498",
      Ukraine: "804",
      Albania: "008",
      "Bosnia and Herzegovina": "070",
      Croatia: "191",
      Serbia: "688",
      "North Macedonia": "807",
      Belarus: "112",
      Niger: "562",
      Angola: "024",
      Benin: "204",
      "Burkina Faso": "854",
      Burundi: "108",
      Cameroon: "120",
      Chad: "148",
      Comoros: "174",
      Congo: "178",
      "Congo Democratic Republic": "180",
      "Cote d'Ivoire": "384",
      Eritrea: "232",
      Eswatini: "748",
      Gabon: "266",
      Gambia: "270",
      Guinea: "324",
      Guyana: "328",
      Lesotho: "426",
      Madagascar: "450",
      Maldives: "462",
      Namibia: "516",
      Rwanda: "646",
      "Sao Tome and Principe": "678",
      "Timor-Leste": "626",
      Togo: "768",
      Turkmenistan: "795",
    };

    g.selectAll(".country")
      .data(countries.features)
      .enter()
      .append("path")
      .attr("class", "country")
      .attr("d", path)
      .attr("fill", (d) => {
        const countryName = Object.keys(countryNameToId).find(
          (name) => countryNameToId[name] === d.id
        );
        if (countryName && violenceData[countryName]) {
          return colorScale(violenceData[countryName]);
        }
        return "#e0e0e0";
      })
      .attr("stroke", "#ffffff")
      .attr("stroke-width", 0.3)
      .attr("stroke-linejoin", "round")
      .attr("stroke-linecap", "round")
      .style("cursor", "pointer")
      .on("mouseover", function (event, d) {
        d3.select(this)
          .attr("stroke", "#1f2937")
          .attr("stroke-width", 2)
          .raise();
        const countryName = Object.keys(countryNameToId).find(
          (name) => countryNameToId[name] === d.id
        );
        if (countryName && violenceData[countryName]) {
          tooltip
            .style("opacity", 1)
            .html(
              `<strong>${countryName}</strong><br/>Violence Score: ${violenceData[
                countryName
              ].toFixed(2)}%`
            );
        }
      })
      .on("mousemove", function (event) {
        tooltip
          .style("left", event.pageX + 10 + "px")
          .style("top", event.pageY - 10 + "px");
      })
      .on("mouseout", function () {
        d3.select(this)
          .attr("stroke", "#ffffff")
          .attr("stroke-width", 0.3)
          .lower();
        tooltip.style("opacity", 0);
      });
    // Expose update function globally
    window.updateHeatmap = function(region, country) {
        const applyUpdate = (selectedCountry) => {
          g.selectAll(".country")
            .transition().duration(750)
            .style("opacity", 1)
            .attr("fill", (d) => {
              const countryName = Object.keys(countryNameToId).find(
                (name) => countryNameToId[name] == d.id
              );
              
              // Determine if this country is "selected"
              let isSelected = false;
              if (!selectedCountry || selectedCountry === 'All Countries') {
                  isSelected = true;
              } else if (Array.isArray(selectedCountry)) {
                  isSelected = selectedCountry.includes(countryName);
              } else {
                  isSelected = countryName === selectedCountry;
              }

              // If selected and has data, show color. Otherwise grey.
              if (isSelected && countryName && violenceData[countryName]) {
                return colorScale(violenceData[countryName]);
              }
              return "#e0e0e0";
            });
        };

        if (country && country !== "All Countries") {
            applyUpdate(country);
        } else if (region && region !== "All Regions") {
            fetch(`/api/countries?region=${encodeURIComponent(region)}`)
                .then(res => res.json())
                .then(countries => {
                    applyUpdate(countries);
                })
                .catch(err => console.error("Error fetching countries for region:", err));
        } else {
            applyUpdate(null);
        }
    };
  })
  .catch((error) => {
    console.error("Error loading map:", error);
    document.getElementById("worldHeatmap").innerHTML =
      '<div class="bg-red-50 text-red-700 p-5 rounded-lg border-l-4 border-red-600">Failed to load world map data. Error: ' +
      error.message +
      "</div>";
  });

// Zoom button handlers
d3.select("#zoom-in").on("click", () => {
  svg.transition().call(zoom.scaleBy, 1.5);
});

d3.select("#zoom-out").on("click", () => {
  svg.transition().call(zoom.scaleBy, 0.67);
});

d3.select("#zoom-reset").on("click", () => {
  svg.transition().call(zoom.transform, d3.zoomIdentity);
});
