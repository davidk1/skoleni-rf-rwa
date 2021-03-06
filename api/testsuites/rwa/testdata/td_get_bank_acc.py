# ocekavana odpoved po provolani detailu bankovniho uctu vychoziho uzivatele Katharina_Bernier
# pro testovani jineho uzivatele je nutne pouzit jemu odpovidajici testovaci data
# ocekavana odpoved je slovnik s detaily bankovniho uctu a kontroluje se 1:1 s odpovedi z api

request_method = 'get'
endpoint = 'bankAccounts'

expected_response = {
   "results": [
      {
         "id": "RskoB7r4Bic",
         "uuid": "a45f1803-b845-42aa-9142-f5f80ea09416",
         "userId": "t45AiwidW",
         "bankName": "O'Hara - Labadie Bank",
         "accountNumber": "6123387981",
         "routingNumber": "851823229",
         "isDeleted": False,
         "createdAt": "2020-05-09T07:57:26.947Z",
         "modifiedAt": "2020-05-21T22:18:50.916Z"
      }
   ]
}
