import requests
commands = {
    "Geraetetyp": "FF00",
    "Geraetenummer": "0600",
    "SW-Version": "0100",
    "Inbetriebnahmedatum": "0E00",
    "Betriebsstundenzaehler": "2500",
    "Kundendienst-Serviceadresse": "5800",
    "Wunschwasserhaerte": "5100",
    "Salzvorrat": "5600",
    "Salzreichweite": "5700",
    "Salzreichweite": "5700",
    "Gesamtwassermenge": "2800",
    "Weichwassermenge": "2900",
    "Tagesstatistik": "FB00",
    "Wochenstatistik": "FC00",
    "Monatsstatistik": "FD00",
    "Jahresstatistik": "FE00",
}
api_url = "http://admin:Connectivity@192.168.42.145/api/rest/"

def get_val(text: str, byte: int, byte_len: int) -> int:
    index = byte*2
    big_endian = text[index:index+byte_len*2] 
    little_endian=bytes.fromhex(big_endian)[::-1].hex()
    return int(little_endian, 16)

def get_text(text: str, byte: int, byte_len: int) -> str:
    index = byte*2
    big_endian = text[index:index+byte_len*2] 
    return bytearray.fromhex(big_endian).decode()

def loop_api():
    for index, item in enumerate(commands):
        print(item)
        url = api_url + commands[item]
        response = requests.get(url)
        res =  response.json()
        print("Scanning "+ item)
        print(res["data"])
        if item == "Salzvorrat":
            print("Restmenge:",str(get_val(res["data"],0,2)/1000)+" kg")
            print("Resttage:",str(get_val(res["data"],2,2))+" Tage")
        else:
            print(res)


res = {"data": "0600",}
print("Wunschwasserhaerte:",str(get_val(res["data"],0,2))+" Grad dH")

res = {"data": "f6541100",}
print("Restmenge:",str(get_val(res["data"],0,2)/1000)+" kg")
print("Resttage:",str(get_val(res["data"],2,2))+" Tage")

res = {"data": "64d90100",}
print("Geraetenummer:",str(get_val(res["data"],0,4)))

res = {"data": "6b1502",}
print("SW-Version:",str(get_val(res["data"],0,3)))
print("SW-Version:",str(int(res["data"],16)))

res = {"data": "060c7500",}
print("Minuten:",str(get_val(res["data"],0,1)))
print("Stunden:",str(get_val(res["data"],1,1)))
print("Tage:",str(get_val(res["data"],2,2)))

res = {"data": "2b343920373139352036393235313720",}
print("Service-Kontakt:",str(get_text(res["data"],0,16)))

res = {"data": "EC221000",}
print("Wassermenge:",str(get_val(res["data"],0,4)/1000)+" Kubikmeter")

res = {"data": "2EDC0000",}
print("Weichwassermenge:",str(get_val(res["data"],0,4)/1000)+" Kubikmeter")

"""
Statistik-Device:
Auswahl Tag, anzeige Tagesstatistik
Auswahl KW: Anzeige KW-Statistik
...
Date-Picker?

Verbrauchszähler: Tagesstatistik addieren und als increasing darstellen

Momentanverbrauch: Differenzen Wassermenge je Zeiteinheit (scanintervall) auftragen
"""
