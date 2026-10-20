DraveLink v0.6
==============
Chat en bestanden delen op je eigen netwerk (LAN) - zonder internet, zonder cloud.
Onderdeel van de Dravenlock-reeks.

Hoe het werkt
-------------
Een pc draait DraveLink = ALLEEN de server. De app toont een webadres en wie er
verbonden is (een serverconsole). Iedereen die wil chatten - OOK JIJ - doet dat via
de BROWSER met een gekozen naam. Je hoeft op de andere apparaten niets te installeren.

- Start DraveLink op een pc. Bovenin staat een webadres, bijv. http://192.168.1.50:8080/
- Wil je zelf meechatten? Klik op de pc op 'Open in browser'.
- Open hetzelfde adres op een ander apparaat op HETZELFDE wifi en kies een naam.
- In de console zie je live wie er verbonden is en wat er in de groep gebeurt.
  (Privegesprekken blijven prive en staan NIET in de serverlog.)

Chatten en bestanden
--------------------
In de browser: klik 'Groep' voor iedereen, of een naam voor 1-op-1. Met het paperclip-
icoon stuur je een bestand. Afbeeldingen (png/jpg/gif/webp...) worden direct getoond;
andere bestanden kun je downloaden.

Alleen testen (zonder tweede apparaat)
--------------------------------------
Open het webadres in TWEE browsertabbladen met verschillende namen (of gebruik
'Open in browser' plus een tweede tabblad). Zo chat je met jezelf om alles te proberen.

Snel starten (zonder bouwen)
----------------------------
1. Pak deze map uit.
2. Dubbelklik run.bat (de eerste keer installeert hij zichzelf, eenmalig).
3. Klik 'Open in browser' en/of deel het webadres met je andere apparaten.

Een losse .exe maken (portable)
-------------------------------
Dubbelklik bouw-exe.bat -> daarna staat dist\DraveLink.exe klaar (onefile).

Bestanden in deze map
---------------------
- dravelink.py      het programma (alles in een bestand)
- run.bat           starten (installeert zichzelf de eerste keer)
- herstel.bat       installatie-omgeving opnieuw opbouwen als er iets hapert
- bouw-exe.bat      maakt een losse DraveLink.exe (onefile)
- dravelink.spec    bouwinstellingen voor PyInstaller
- maak_icoon.py     maakt het programma-icoon
- requirements.txt  benodigde onderdelen (PyQt6)

Instellingen
------------
Klik op 'Instellingen...' voor de webpoort, de map voor gedeelde bestanden en de taal
(standaard volgt hij je systeemtaal; Nederlands als basis).

Problemen oplossen
------------------
- Kan een ander apparaat er niet bij? Zorg dat beide op HETZELFDE netwerk zitten,
  dat de Windows-firewall DraveLink toestaat, en dat je netwerk op 'Prive' staat.
- De server-pc moet aan blijven zolang anderen verbonden zijn.
- De Snelgids (knop rechtsboven) legt alles stap voor stap uit.

Gemaakt met zorg door Dravenlock - service@dravenlock.nl


Toegangscode (v0.5)
-------------------
Zet in Instellingen een Toegangscode als DraveLink (per ongeluk) van buiten je netwerk
bereikbaar is. De browser vraagt de code 1x en onthoudt 'm; daarna is alles beschermd
(de chat en de gedeelde bestanden). Leeg = open (alleen veilig op je eigen netwerk).
