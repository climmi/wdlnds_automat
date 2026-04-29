# Woodlands Automat Style Bible

## Richtung

Arbeitsrichtung: `Sunny Pixel Show Control`

Der Automat ist kein dunkles Neon-Arcade-Spiel mehr. Er ist ein heller, sonniger Woodlands-Moment:
Pixelgelaende, DJ-Platz, Tanzflaeche, Menschen, Musik und direkte Button-Energie.

Ziel:

- hell
- sonnig
- physisch
- direkt
- gut lesbar
- warm und charmant
- performant auf Raspberry Pi
- eher Festival-Spielzeug als App

Das Spiel soll sich anfuehlen wie ein kleiner Woodlands-Automat auf dem Gelaende: Man steht davor, drueckt im richtigen Moment die Buttons, die Crowd reagiert sichtbar, und das DJ-Set wird dadurch besser.

## Kerngefuehl

Die drei wichtigsten Begriffe:

- `Stimmung`
- `Timing`
- `Klarheit`

Produktentscheidung:

- Es gibt ein zentrales Minigame: `Show Control`.
- Die alten drei Minigames sind verworfen, weil sie zu nah an derselben Mechanik waren.
- Das Spiel zeigt eine Pixel-Szene mit Woodlands-Gelaende, Buehne/DJ-Platz, Dancefloor und Crowd.
- Die Spielperson steuert Show-Momente passend zur Musik.
- Die Crowd ist die wichtigste Rueckmeldung: Sie kommt auf die Tanzflaeche, tanzt staerker, wird happy oder langweilt sich.
- Jede Runde ist ein `DJ SET` von einem zufaelligen Act aus echten Woodlands-Lineups.
- Die Runde laeuft zu einem echten Audio-Track und hat ein geplantes Ende nach ca. 3-5 Minuten.

Jeder Screen muss auf diese Fragen eine klare Antwort geben:

1. Was soll ich jetzt druecken?
2. Habe ich gut getroffen?
3. Wie reagiert die Crowd?

## Aktuelles Minigame: Show Control

Pitch:
Die Show laeuft. Noten fallen in drei transparenten Lanes von oben auf die Button-Zonen. Die Spielperson drueckt, haelt oder kombiniert die drei Buttons passend zu Beat, Melody und Pattern des Tracks. Gute Eingaben fuellen die Tanzflaeche, schlechte Eingaben lassen die Stimmung kippen.

Button-Rollen:

- links = Crowd / Move
- mitte = Drop / Center
- rechts = FX / Farbe
- Start kann im Spiel als mittlerer Button mitzaehlen, wenn noetig.

Regeln:

- Drei Lanes laufen vertikal von oben nach unten.
- Die Lanes sind transparent, damit Gelaende und Crowd sichtbar bleiben.
- Notes sollen ueber die Button-Zone hinaus weiter nach unten laufen, damit Timing-Fehler sichtbar bleiben.
- Button-Felder brauchen keine Textlabels wie `L`, `M`, `R`; Farben reichen.
- Zwei Buttons gleichzeitig sind erlaubt.
- Im normalen Modus nie mehr als zwei Buttons gleichzeitig, weil eine Person zwei Haende hat.
- Drei-Button-Momente sind nur als spaetere Spezialidee vorgesehen.
- Hold-Notes belegen ihre Lane komplett: Waehrend eines Holds darf auf derselben Lane keine zusaetzliche Tap-Note erscheinen.

Input-Arten:

- `Tap`
  Kurzer Druck im richtigen Timing-Fenster.
- `Double Tap / Chord`
  Zwei Buttons gleichzeitig, wenn Beat und Melodie es tragen.
- `Hold`
  Button am Anfang des Balkens druecken und bis zum Ende halten.
- `Hold + Tap`
  Eine Taste halten, waehrend auf einer anderen freien Lane weitere Taps kommen.
- `Pattern`
  Kurze Folgen, die aus Beat- oder Melodie-Strukturen abgeleitet werden.

Wichtig:
Hold darf nie bedeuten, dass dieselbe Taste waehrenddessen noch einmal gedrueckt werden muss. Hold + Tap ist nur auf anderen Lanes erlaubt.

## Audio- und Pattern-Regeln

Das Spiel nutzt Audioanalyse, um Timing-Cues zu erzeugen.

Ziele der Analyse:

- BPM erkennen.
- Beat-Positionen erkennen.
- starke Onsets finden.
- grobe Frequenzbereiche als Button-Logik nutzen:
  - Low / Drums / Kick eher links
  - Mid / Groove / Main eher mitte
  - High / Melodie / FX eher rechts
- aus Beat und Melodie ein Pattern bauen, das sich musikalisch anfuehlt.

Schwierigkeitsverlauf:

- Die ersten 10 Sekunden sind Ankommen.
- Von 10-30 Sekunden steigt die Schwierigkeit spuerbar, aber fair.
- Danach gibt es einfache, mittlere und schwere Segmente.
- Schwierige Segmente duerfen schnelle Folgen, Chords, Holds und Hold+Tap kombinieren.
- Leichte Segmente bleiben regelmaessig und gut lesbar.
- Der Track soll nach ca. 3-5 Minuten enden, damit die Runde einen Abschluss hat.

Vermeiden:

- generische Takt-Beep-Sounds
- generische Tastendruck-Beep-Sounds
- zufaellige Noten, die sich nicht nach Musik anfuehlen
- Hold-Konflikte auf derselben Lane
- sofort ueberfordernde Patterns am Trackanfang

## Crowd-Regeln

Die Crowd ist das emotionale Zentrum.

Start:

- Erst kleine Grueppchen.
- Figuren sind sichtbar genug, nicht winzig.
- Sie stehen nicht einfach fertig auf der Flaeche, sondern kommen von unten links und unten rechts auf den Dancefloor.

Aufbau:

- Mit Streak und guter Stimmung kommen mehr Leute dazu.
- Aus kleinen Gruppen wird eine volle Crowd.
- Gute Treffer machen Figuren happy.
- Fehler machen Figuren bored oder reduzieren Bewegung.
- Bei guter Combo tanzt die Menge staerker, schneller und sichtbarer.

Charakter-Zustaende:

- `normal`
  Startzustand und neutrale Stimmung.
- `happy`
  bei guten Treffern, Streaks, sauber gehaltenen Holds.
- `bored`
  bei Fehlern, losgelassenen Holds, zu frueh/zu spaet.

Sprites:

- Die Normie-Charaktervarianten aus `graphic/charakters/normie 01/` sind die aktuelle Referenz.
- Figuren muessen gross genug sein, dass der Zustand auch auf Distanz lesbar ist.
- Viele Figuren duerfen dieselbe Basisgrafik nutzen, aber mit kleinen Positions-, Timing- und Skalierungsunterschieden.

## Visuelle Regeln

### Hintergrund

- Das Woodlands-Levelbild ist die Hauptszene.
- Die Szene soll hell, sonnig und freundlich wirken.
- Keine schwarzen Navigationsbereiche.
- Keine dunklen Fullscreen-Overlays.
- Keine CRT-, Grid- oder Neon-Overlays.
- Keine dekorativen Effekte ueber der ganzen Szene.
- UI liegt schlicht auf hellen Weiss-/Beige-Flaechen.

Vermeiden:

- flimmernde Linien
- billige CRT-Optik
- Neon-Glow als Grundlook
- dunkle Arcade-Bedrohung
- Partikelwolken ohne spielerische Bedeutung

### UI

- Schlicht weiss/beige.
- Schwarze oder dunkelbraune Pixelschrift.
- Klare Konturen, wenig Deko.
- Kein unnötiges Raster.
- Keine Karten-in-Karten-Optik.
- Die Szene hat Vorrang vor UI.

HUD:

- klein halten
- Score und Stimmung nicht mitten in den Spielbereich legen
- DJ-Set/Artist darf sichtbar sein, aber nicht wichtiger als Lanes und Crowd
- kurze Labels wie `PERFEKT`, `GUT`, `HALTEN`, `LOSGELASSEN`

### Lanes und Buttons

- Lanes sind transparent.
- Button-Zonen sind farbig und stabil positioniert.
- Keine Textlabels in den Buttonfeldern.
- Farben muessen klar unterscheidbar sein.
- Notes und Hold-Balken muessen bis unter die Hit-Zone sichtbar bleiben.
- Trefferfenster ist visuell eindeutig, aber nicht schwer oder dunkel.

### Farbe

Basis-Palette:

- Sonnenflaeche: `#FFFDF0`
- Beige UI: `#F4EAD8`
- Holz/Braun fuer Konturen: `#4B3826`
- Schwarze Pixelschrift: `#171814`
- Weicher Text: `#5C4F38`
- Himmelblau: `#4B9AE1`
- Sonnengelb: `#F5AE39`
- Warmes Rot: `#EB604E`
- Happy-Gruen: `#59B560`

Verwendung:

- Blau fuer Bewegung/Crowd.
- Gelb fuer Drop/Fokus/Erfolg.
- Rot fuer Fehler oder schwache Stimmung.
- Gruen fuer happy Crowd und gute Stimmung.

Regeln:

- Kontrast wichtiger als Dekoration.
- Pro Screen maximal 2 dominante Akzentfarben.
- Keine einfarbige Neonwelt.
- Keine dunkle Grundstimmung im aktuellen Spiel.

## Typografie

- Pixelschrift verwenden.
- Kurz, klar, direkt.
- Keine langen Erklaerungen im Spiel.
- HUD-Text ist sekundär gegenueber Spielobjekten.

Gute Woerter:

- `JETZT`
- `HALTEN`
- `PERFEKT`
- `GUT`
- `OOPS`
- `LOSGELASSEN`
- `GEHALTEN`
- `DJ SET`

Vermeiden:

- erklaerende Saetze waehrend des Spiels
- Text auf unruhigem Hintergrund
- zu viele konkurrierende Labels

## Bewegung

Bewegung ist Feedback, nicht Dekoration.

Gute Bewegungsarten:

- Notes fallen sauber nach unten.
- Hold-Balken zeigt die komplette Dauer.
- Figuren laufen von unten links/rechts auf den Dancefloor.
- Crowd bounced je nach Stimmung.
- Happy-Figuren tanzen groesser.
- Bored-Figuren bewegen sich weniger.
- Button-Felder reagieren sofort auf Input.

Vermeiden:

- Screen-Shake
- White-Flashes
- dunkle Treffer-Overlays
- Glow-Massen
- permanente Fullscreen-Effekte

## Sound

Aktuelle Regel:

- Der Track selbst ist die Musik und der Timing-Geber.
- Keine generischen Beeps fuer Takt.
- Keine generischen Beeps beim Tastendruck.
- Feedback entsteht primaer visuell ueber Crowd, Hit-Labels und Stimmung.

Spaeter moeglich:

- dezente, musikalisch passende UI-Sounds
- nur wenn sie den Track nicht stoeren
- keine Arcade-Standard-Beep-Sounds

## Artist- und Show-Regeln

Jede Runde heisst nicht allgemein `Woodlands Show`, sondern ist ein `DJ SET` eines zufaelligen Acts.
Die Namen sollen nach Festival-Lineup klingen, aber fiktiv sein. Keine echten Act-Namen 1:1 verwenden.

Aktuelle fiktive Artist-Liste:

- Konfluxia
- Mako
- Cocoluma
- Elbarto
- Pabu
- Felderkern
- ELX Sounds
- Dotto
- DJ KRSX
- Nebelluft
- Sira Wald
- Melbo & Finke
- Hurst Haller
- Sinamoon
- Carlo Bonaro
- Vektor Ruiz
- Susi Pola
- Saburo
- Nina Osono
- Madrio
- Stacy 8_8
- Marlon Marea
- Dub Fuzz
- Flux
- Bendji
- Hillbilly HiFi feat. Longfinger
- Luisa Lakuna
- Singing Stone
- Ayo
- Tober & Tabor

Lineup-Kontext:

- Woodlands meets Moyn Festival, Juli 2025
- WOODLANDS x Bebop Open Air, September 2025
- Weitere Acts der Saison 2025
- Wolke 17, Mai 2026
- Weedbeat x Woodlands Special Edition, Juli 2026
- Einzeltermine und Resident-Vibes

## Screen-Regeln

Startscreen:

- Kein Text wie `Dann startet die Tanzflaeche`.
- Kurzer, klarer Einstieg.
- Hell, ruhig, direkt.

Navigation:

- schlicht weiss/beige
- schwarze Pixelschrift
- keine schwarzen Flaechen
- keine Grid-Overlays
- keine Neon-Effekte

Spielscreen:

- Szene zuerst.
- Lanes und Notes muessen lesbar bleiben.
- Crowd darf nie komplett von UI verdeckt werden.
- Hit-Zone unten, aber Notes laufen sichtbar weiter bis zum unteren Rand.

## Performance-Regeln fuer Raspberry Pi

- Hintergrund moeglichst cachen.
- Grosse Alpha-Flaechen sparsam einsetzen.
- Keine permanenten Fullscreen-Overlays.
- Keine Blur-/Glow-Tricks.
- Animation vor allem ueber Sprites, Positionen und kleine UI-Zustandswechsel.
- Pixelgrafiken skalieren, aber nicht staendig neu berechnen.

Faustregel:
`Nur das animieren, was Bedeutung hat.`

## Spaeter Vormerken

Nicht jetzt bauen, aber als Idee behalten:

- Spezial-Schwierigkeitsgrad mit Drei-Button-Momenten.
- Drei-Button-Moment als Party-Gag: zweite Person hilft, oder man drueckt kreativ mit Kopf/Fuss.
- Mehr Charaktertypen in der Crowd.
- Mehr echte Tracks mit eigener Cue-Analyse.
- Manuelle Chart-Korrektur fuer besonders wichtige Songs.
- Schwierigkeitsgrade fuer Solo, Crew und Party.

## Nicht Mehr Aktuelle Richtung

Diese alten Richtungen sind verworfen oder nur noch Inspirationsmaterial:

- Drei separate Minigames mit fast gleicher Mechanik.
- Dunkle Beatline-/Light-Ops-Neonoptik.
- CRT-Raster, Scanlines, schwarze Arcade-Flächen.
- Generische Beep-basierte Rhythmusmechanik.
- Runner-Optik als Kernspiel.

Die aktuelle Richtung ist eindeutig:
`Show Control` als sonniges Pixel-DJ-Set mit wachsender Crowd und musikalisch erzeugten Lane-Cues.
