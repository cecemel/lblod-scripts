SELECT DISTINCT
  ?g
  ?address
  ?addressStreet
  ?addressGemeenteNaam
  ?addressGemeenteLand
  ?addressGemeentePostCode
  ?addressGemeenteNummer
  ?site
  WHERE {
  GRAPH ?g {
    ?address a <http://www.w3.org/ns/locn#Address>;
        <http://www.w3.org/ns/locn#thoroughfare> ?addressStreet;
        <https://data.vlaanderen.be/ns/adres#gemeentenaam> ?addressGemeenteNaam;
        <https://data.vlaanderen.be/ns/adres#land> ?addressGemeenteLand;
        <http://www.w3.org/ns/locn#postCode> ?addressGemeentePostCode;
        <https://data.vlaanderen.be/ns/adres#Adresvoorstelling.huisnummer>
          ?addressGemeenteNummer.
  }

  ?site a <http://www.w3.org/ns/org#Site>;
    <https://data.vlaanderen.be/ns/organisatie#bestaatUit> ?address.

  FILTER NOT EXISTS {
    ?address <https://data.vlaanderen.be/ns/adres#verwijstNaar> ?foo.
  }
}


https://loket.lblod.info/adressenregister/match?
municipality=Temse
zipcode=9140
thoroughfarename=Velle
housenumber=123


[
  {
    "@type": "Adres",
    "identificator": {
      "id": "https://data.vlaanderen.be/id/adres/1107867",
      "naamruimte": "https://data.vlaanderen.be/id/adres",
      "objectId": "1107867",
      "versieId": "2024-10-31T14:33:44+01:00"
    },
    "detail": "https://api.basisregisters.vlaanderen.be/v2/adressen/1107867",
    "huisnummer": "123",
    "volledigAdres": {
      "geografischeNaam": {
        "spelling": "Velle 123, 9140 Temse, België",
        "taal": "nl"
      }
    },
    "adresStatus": "inGebruik",
    "land": "België"
  }
]



[

{'graph': 'http://mu.semte.ch/graphs/administrative-unit',
'address': 'http://data.lblod.info/id/adressen/67ECFD27F5AB773B5FCCCF15', 'addressStreet': 'Frans Masereellaan', 'addressGemeenteNaam': 'Blankenberge', 'addressGemeenteLand': 'België', 'addressGemeentePostCode': '8370', 'addressGemeenteNummer': '9', 'site': '', 'addressRegister': 'https://data.vlaanderen.be/id/adres/2223326'} ,

{'graph': http://foo',
'address': 'http://data.lblod.info/id/adressen/bar', 'addressStreet': baz', 'addressGemeenteNaam': 'boem', 'addressGemeenteLand': 'france', 'addressGemeentePostCode': '8370', 'addressGemeenteNummer': '9', 'site': '', 'addressRegister': 'https://data.vlaanderen.be/id/adres/zoomba'} ,
]


I want you to write a function to `.sparql` file that based on the array input above INSERT DATA grouped per graph is written.
So one graph can have multiple entries. Please read carefully the sample input
```
INSERT DATA {
 GRAPH <http://mu.semte.ch/graphs/administrative-unit> {
   <http://data.lblod.info/id/adressen/67ECFD27F5AB773B5FCCCF15> <https://data.vlaanderen.be/ns/adres#verwijstNaar> <https://data.vlaanderen.be/id/adres/2223326>
   .... OTHER STATEMENTS FROM THE INPUT
 }
}

;

INSERT DATA {
 GRAPH <http://foo> {
   <http://data.lblod.info/id/adressen/bar> <https://data.vlaanderen.be/ns/adres#verwijstNaar> <https://data.vlaanderen.be/id/adres/2223326>
   .... OTHER STATEMENTS FROM THE INPUT
 }
}
```


https://api.basisregisters.vlaanderen.be/v2/adressen?GemeenteNaam=Antwerpen&Postcode=2100&Straatnaam=Mattheus Corvenstraat&Huisnummer=110&
