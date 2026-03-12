# Q-CODES and Filters

Here are the Q) subject codes most useful to a drone pilot, based on ICAO/FAA International NOTAM Q‑code tables. 

The Q‑line structure is standardized:   Q) CZYZ/QOLAS/IV/M/AE/000/014/4447N07822W005 

2nd/3rd letters = subject, 

4th/5th = status.  



The Q‑line fields are defined as FIR / NOTAM Code / Traffic / Purpose / Scope / (Lower / Upper) / Coordinates+Radius.

**Q) CZYZ / QOLAS / IV / M / AE / 000 / 014 / 4447N07822W005**

- **CZYZ** = FIR (Toronto FIR) is default. The first field in the Q‑line is always the FIR that contains the subject. 
- **QOLAS** = NOTAM code (5 letters)
  - **Q** is always there as a qualifier
  - **OL**  2nd/3rd letters) = ***Obstacle lights***
  - **AS** (4th/5th letters) = ***Unserviceable***
  
- **IV** = Traffic: applies to **IFR and VFR**. (Traffic qualifiers are I, V, or IV) 
- **M** = Purpose: **Miscellaneous** (not for briefing but available on request)
- **AE** = Scope: **Aerodrome + En‑route** (combined scope is allowed)
- **000 / 014** = Lower/Upper limits (000 = surface; 014 = 1,400 ft). 
- **4447N07822W005** = center point and **5 NM** radius. 

So this NOTAM is **obstacle lights unserviceable**, relevant to **IFR & VFR**, with **miscellaneous purpose**, and scoped to **aerodrome + en‑route**, covering **surface to 1,400 ft** within **5 NM** of the given coordinates.



### **Must‑include (obstacles / lighting)**

OB = Obstacle (e.g., towers, cranes, wires)
*<u>OL = Obstacle lights*</u> 

### Must‑include (warnings / activities)
These are all under Navigation Warnings: Warnings (W):

WA Air display
WB Aerobatics
WC Captive balloon/kite
WD Demolition of explosives
WE Exercises
WG Glider flying
WH Blasting
WJ Banner/target towing
WL Free balloon
WM Missile/gun/rocket firing
WP Parachute / paragliding / hang gliding
WR Radioactive/toxic materials
WS Burning/blowing gas
WT Mass movement of aircraft
WU Unmanned aircraft
WV Formation flight
WW Significant volcanic activity
WY Aerial survey
WZ Model flying
(faa.gov)
Must‑include (regulatory / airspace restrictions)
These are under Navigation Warnings: Airspace Restrictions (R):

RA Airspace reservation
RD Danger area
RM Military operating area
RO Overflying restrictions
RP Prohibited area
RR Restricted area
RT Temporary restricted area

<u>Optional (airspace structure)</u>
If you want airspace structure changes that can affect drone ops:

AC Class B/C/D/E surface area (CTR)
AD ADIZ
AE Control area (CTA)
AF FIR
AT TMA
AZ ATZ





### more logic

Yes—these are all ICAO Q‑codes, and NAV CANADA uses the ICAO format (per TC AIM and NAV CANADA’s ICAO transition). 
So the authoritative references are ICAO Doc 8400 / Doc 8126 (not freely published), and publicly available mirrors like 
FAA’s Appendix B (International NOTAM Q Codes), plus TC AIM’s description of the Q‑item fields. ([tc.canada.ca](https://tc.canada.ca/sites/default/files/2024-09/aim-2024-2_map-e.pdf?utm_source=openai))

Below is a **Canadian‑format interpretation** of the codes you listed, using the ICAO Q‑code tables (subject = 2nd/3rd letters, condition = 4th/5th letters):

**QFAXX**

- **QF** = AGA **Facilities/Services** (ICAO subject category). ([icao.int](https://www.icao.int/WACAF/Documents/Meetings/2018/AIS to AIM/Volume III Appendix 6 2018-02-19.pdf?utm_source=openai))
- **XX** = condition not covered by the standard list; use plain language. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
  **Meaning:** Facilities/services issue, condition is “other/unspecified,” so details are in free text.

**QPIAU**

- **QP** = ATM **Air Traffic Procedures** (ICAO subject category).
- **PI** = **Instrument approach procedure**. 
- **AU** = **Not available**. 
  **Meaning:** Instrument approach procedure **not available**.

**QPMCH**

- **QP** = ATM **Air Traffic Procedures**. ([icao.int](https://www.icao.int/WACAF/Documents/Meetings/2018/AIS to AIM/Volume III Appendix 6 2018-02-19.pdf?utm_source=openai))
- **PM** = **Aerodrome operating minima**. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
- **CH** = **Changed**. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
  **Meaning:** Aerodrome operating minima **changed**.

**QLYXX**

- **QL** = AGA **Lighting facilities**. ([icao.int](https://www.icao.int/WACAF/Documents/Meetings/2018/AIS to AIM/Volume III Appendix 6 2018-02-19.pdf?utm_source=openai))
- **LY** = **Taxiway edge lights**. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
- **XX** = condition not covered; use plain language. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
  **Meaning:** Taxiway edge lights issue, condition is “other/unspecified.”

**QMXXX**

- **QM** = AGA **Movement and landing area**. ([icao.int](https://www.icao.int/WACAF/Documents/Meetings/2018/AIS to AIM/Volume III Appendix 6 2018-02-19.pdf?utm_source=openai))
- **MX** = **Taxiway(s)**. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
- **XX** = condition not covered; use plain language. ([faa.gov](https://www.faa.gov/air_traffic/publications/atpubs/notam_html/appendix_b.html))
  **Meaning:** Taxiway issue, condition is “other/unspecified.”





Obstacles / Lighting
Warnings / Activities (W*)
Airspace Restrictions (R*)
Airspace Structure (A*)
