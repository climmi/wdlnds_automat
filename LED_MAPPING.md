# LED Mapping

## Index-Konvention

Die ersten vier LEDs wurden nachtraeglich vor die eigentliche Zaehllinie gesetzt.
Sie werden deshalb als Sonder-LEDs behandelt:

| Physische LED | Logischer Index | Funktion |
| --- | ---: | --- |
| 1 | -3 | Button rechts |
| 2 | -2 | Button mitte |
| 3 | -1 | Button links |
| 4 | 0 | Button oben / Start |

Ab der danach folgenden LED beginnt die normale Mapping-Zaehlung:

| Genannte Zahl | Physische LED am Strip | Logischer Index |
| ---: | ---: | ---: |
| 1 | 5 | 1 |
| 2 | 6 | 2 |
| 3 | 7 | 3 |

Formel:

```text
physische_led = genannte_zahl + 4
logischer_index = genannte_zahl
```

Wichtig:
Wenn beim weiteren Mapping eine Zahl genannt wird, ist damit der `logische_index` gemeint.
Der Firmware-Array-Index ist bei NeoPixel nullbasiert:

```text
firmware_index = physische_led - 1
```

## Leuchtbereiche

Alle Bereiche in dieser Tabelle verwenden die genannte Zahl als logischen Index.
Die physische LED am Strip ist jeweils um `+4` verschoben.
Der Firmware-Index ist nullbasiert und damit `logischer_index + 3`.

Achtung:
Der Strip muesste nach aktuellem Stand `172` LEDs inklusive Button-LEDs haben.
Mit der `+4`-Verschiebung waere die hoechste sichere genannte Zahl damit `168`.
Falls ein Bereich bis zur genannten LED `169` geht, muss dieser letzte Abschnitt beim Durchtesten noch einmal geprueft werden.

| Logische LEDs | Physische LEDs | Firmware-Index | Bereich |
| ---: | ---: | ---: | --- |
| 1-2 | 5-6 | 4-5 | Teil links |
| 3-4 | 7-8 | 6-7 | Volle links |
| 5-22 | 9-26 | 8-25 | 100 Venus Multi 55 Mitte |
| 23-24 | 27-28 | 26-27 | Multi |
| 25-26 | 29-30 | 28-29 | Serie |
| 27-28 | 31-32 | 30-31 | 40 Mitte |
| 29-30 | 33-34 | 32-33 | 50 Mitte |
| 31-32 | 35-36 | 34-35 | 30 Mitte |
| 33-35 | 37-39 | 36-38 | Zwei Sonnen = 4 Mitte |
| 36-38 | 40-42 | 39-41 | Eine Sonne = 3 Mitte |
| 39-41 | 43-45 | 42-44 | Drei Muenzen = 3 Mitte |
| 42-44 | 46-48 | 45-47 | Zwei Muenzen = 2 Mitte |
| 45-46 | 49-50 | 48-49 | Gestoert links |
| 47-52 | 51-56 | 50-55 | Start links |
| 53-54 | 57-58 | 56-57 | 50 links |
| 55-56 | 59-60 | 58-59 | 25 links |
| 57-58 | 61-62 | 60-61 | 12 links |
| 59-60 | 63-64 | 62-63 | 6 links |
| 61-62 | 65-66 | 64-65 | 3 links |
| 63-64 | 67-68 | 66-67 | 2,60 DM links |
| 65-66 | 69-70 | 68-69 | 1,30 DM links |
| 67-68 | 71-72 | 70-71 | 0,60 DM links |
| 69-70 | 73-74 | 72-73 | 0,30 DM links |
| 71-72 | 75-76 | 74-75 | 0 Pfennig links |
| 73-74 | 77-78 | 76-77 | Startautomatik an/aus Mitte |
| 75-76 | 79-80 | 78-79 | 0 Pfennig Mitte |
| 77-83 | 81-87 | 80-86 | 20 Mitte |
| 84-90 | 88-94 | 87-93 | 40 Mitte |
| 91-97 | 95-101 | 94-100 | 70 Mitte |
| 98-104 | 102-108 | 101-107 | 1,50 Mitte |
| 105-115 | 109-119 | 108-118 | 3 Mitte |
| 116-126 | 120-130 | 119-129 | 4 Mitte |
| 127-141 | 131-145 | 130-144 | Ausspielung Mitte |
| 142-143 | 146-147 | 145-146 | 0 rechts |
| 144-145 | 148-149 | 147-148 | 20 rechts unten |
| 146-147 | 150-151 | 149-150 | 40 rechts unten |
| 148-149 | 152-153 | 151-152 | 80 rechts |
| 150-151 | 154-155 | 153-154 | 1,60 rechts |
| 152-155 | 156-159 | 155-158 | 2 rechts |
| 156-161 | 160-165 | 159-164 | Stopp rechts |
| 162-163 | 166-167 | 165-166 | 4 rechts |
| 164-165 | 168-169 | 167-168 | 10 rechts |
| 166-167 | 170-171 | 169-170 | 20 rechts oben |
| 168-169 | 172-173 | 171-172 | 40 rechts oben |
