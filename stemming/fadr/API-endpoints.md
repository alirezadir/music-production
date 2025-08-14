https://fadr.com/docs/api-endpoints#create-stem-task

POST /assets/upload2
Create Presigned Upload URL
Create Presigned Upload URL is used to create a URL from which you can upload a file to Fadr's file storage via a subsequent PUT request. The presigned URL you get back gives you temporary write permission for one location in Fadr's file storage.

Request
Field	Description
name	The name of the file that will be uploaded.
extension	The file extension of the file that will be uploaded.
Example request body:

{ "name": "mysong.mp3", "extension": "mp3" }
Response
Field	Description
url	The url for uploading your file via PUT request.
s3path	The s3 path where the file will be stored. You must provide this in a subsequent create asset request.
Example response body:

{
  "url": "https://songtostems-songs-test.s3.us-east-1.amazonaws.com/tmp/62b6798a2945210048ee1a8b/mysong%20mp3-8209cecb-1fbd-4c09-82f4-05d27c2fd3e5.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAQNJIJZWBUANY6EAS%2F20230809%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20230809T161958Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEP7%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJGMEQCIHK5%2Fr6qUo0hYWSx1WOa2TGn%2BpUB1Sei8aC63Zyq%2FJfZAiAB5Pb0xB%2BKgvnMpVBlyS0UmWftNngqlZHxY44qwsPCiCqQBAin%2F%2F%2F%2F%2F%2F%2F%2F%2F%2F8BEAMaDDAyODUzODY4Njg1MSIMVj0k%2F7WP4ZA1tmshKuQD5NgMFw5jmw0sVI76ueEjDZHMTR9MVfx9L8JDpzVzV6QpjTfPtmHdgpgxutWnYEGexOtNkIWVe0uTgk0yt2S9iFU4DU0rGQc4vmLND%2F3cUjl3UtZfV8v1M0F9kmrX22GxwfqyCKboDmePRFbG4j4NA2mrvbI9S3j%2FIRdqG8wafYpwp4QWllPbnIMPazKk2P16067sF%2FiF94Lo4sjjDj4ySqd185bRQWR04xMVjCwpcl3FENrMxa%2BPI0Jigm043MSMS%2FUIrnldFCbgRvtkHLwDTFMLMPoBXnNaK6zhabGI0NXcFZBxZir5EH%2FrNjVc0AT4nn9k5wGkHbMEs%2FWeLIj1sa8rsijH%2F7mXETvteczszP9Wm%2B2RLK63urnyHc603jsblQe6zH%2FvE%2F9%2FQ7adX%2F5GjW5eGn4Nj1sTnWSXNIJ0fyqcMrhoA9tik%2FxkLKsUqa4RERCmaSw2FxZpQ4nPfyQbaKuesi7lnLLtiIaeY2Mc0vCfpt%2FsaryEWIR%2BfQeCcTYqNqVOdYyR85uxh4qWK0vr0%2B%2ByVjpgJjX%2BMlz4FlBZeuve8pMrEVpD7lbcZZMCwRc0ACRjipjeaTiUEbDUk4Ii2MD2jXl8p7sHoSZj%2BH6YAd6vESvRcjWbqzq8ePMLDNJu0ZFdeTCUr86mBjqmAYMU62VV9vcCXrdFPAXlZAVCG8zEQxl52xJ3D%2FhgzswzUgu3cJHpXqcj2%2BclwpNissgD%2B7Jt1eB89zFoNYH0KGV3Hv4qYcyDf969es%2Fnkj74I3Mb2RxUF1itULh9Qu5Cj%2B438klMBiMYm3cCEt4wbCRI2zVr8kojoqjFgFIe6nxv5DasuZFeDCYNs%2Fpchqd9BgGKn7bidaqASABrq73nQmifVKn2K3k%3D&X-Amz-Signature=37e4cf7b3b12bc4b03c8119d08a5bff6e424fde9691204ddc22dabe14e5abaa6&X-Amz-SignedHeaders=host&x-amz-storage-class=INTELLIGENT_TIERING&x-id=PutObject",
  "s3Path": "tmp/62b6798a2945210048ee1a8b/mysong mp3-8209cecb-1fbd-4c09-82f4-05d27c2fd3e5.mp3"
}



PUT <Presigned Upload URL>
Upload File
After you've created a presigned URL via Create Presigned Upload URL, a PUT request is used to upload the file to Fadr's file storage. This request is not made to the Fadr API, but rather to the presigned URL you received.

You must specify the MIME type of the file you are uploading using the Content-Type header on the PUT request - learn more. For example, add the following header if you are uploading an MP3 audio file:

"Content-Type": "audio/mp3"


GET /assets/download/:_id/:type
Create Presigned Download URL
Create Presigned Download URL is used to create a URL from which you can download a file from Fadr's file storage via a GET request. The presigned URL you get back gives you temporary read permission for one file in Fadr's file storage. Create Presigned Download URL is a dynamic route with the path parameters described below.

Path Parameters	Description
_id	The _id property of the asset corresponding to the file you would like to download.
type	Type must be one of "preview", "hqPreview", or "download" corresponding to three audio quality levels/file sizes. Preview is a medium quality MP3, hqPreview is a very high quality MP3, and download is a lossless WAV file. We find that hqPreview is indistinguishable from lossless WAV without sophisticated audio equipment.
Response
Field	Description
url	The url for uploading your file via PUT request.
type	The download quality you selected via the type path parameter.
ext	The file extension of the corresponding file.
key	For use by Fadr.
Example response body:

{
  "url": "https://songtostems-songs-test.s3.us-east-1.amazonaws.com/62b6798a2945210048ee1a8b/90c00b60-f2a7-4326-a943-bd20820d403b.mp3?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Credential=ASIAQNJIJZWB7QZOSOXL%2F20230809%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20230809T171900Z&X-Amz-Expires=3600&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEAEaCXVzLWVhc3QtMSJIMEYCIQDM2hYP4KDcH6Gk8VyWOBcJ4PnfgHB4ihV4J6tG8FddYQIhAL%2FP6ZOa%2F%2BXcPKFnCYRw%2FSVc%2B%2B6ooZIq3GDWvt9dWVJtKpAECKr%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEQAxoMMDI4NTM4Njg2ODUxIgxrCyeaDDVgTS8QbQwq5AMuP6PfyZrAuKjrBwTVehEx9P4cbd4hNCy4kL4Zee8MjwrnL41DEq1XSR%2FEIhqSoA%2BrQzqV1oYrSAVXqz1lQpdDvQgNBUlPBry69SGtcpoJZX8rQPhGAo%2B5o%2FP2ununOcOTY0kAEhpDH86bNURnKjzhiJ6DZhFi3aYhA%2FBM4TuMgArSfeN4%2F5Cl2IADOcVU0mWMe7Vtn5ifcC950C1CzaqaF52Lj%2BPdlOCPO2oqJ5G%2BzC%2FZldPJprRp2dxh3AovqW%2BFVQBRHfEJuAU%2BtgCQJZ%2BAAE%2BmEYXBkXERru2ioAMlZgiJz%2Bn9lnMXRT%2F66bB1tXmkXz5QuW8kgWFwXmRdaGNeRngmbQPfTWCRXr4%2BoT6rzuYux6getDNuBgIjmqAa6cy3ghYT8t08CzJCVxw8EGIuSZNqTvm2wh5tpaCPey68BNLga%2Fon0uPdjMQ7IzBXMXqYgut05jehWSlfzcovNLKfq4RKNtbEgOF3ot1poZ%2F68ASA0TQavJGCZVH94E4pl67DgYoioEFMcdyqVuFJIy8SzZftu%2FDMl%2Fv7%2Fo61f%2B2p%2FJlwXF53lBrP2AWOoR1PowKks4i7mf0Fdbi6zgmu1YX6pffp17LMGk7atR7cccYp%2Fw10dWN71PF50EL9zcQgc8F4y96zMJeEz6YGOqQB4tSZ1yacQpjHdhcJsUwjhGXkoLSKVSgRusZDTkkReM%2Fyfk%2Bf9b9TOjyeNiIK0PVoBVWvVHSyn3lc%2BWlwCRu6i0a5QcOWltn%2FagwImUWnqK6wbtRfzlZxo68G9A2sUMhVHGxztjIXgMJCGcMjeuFz%2F%2FVAWxAH2MVjfVLTUDCd1GoXYR2v8YHtJeu8W3NAhS3EluqhMm7IJsJeDGKw5CIPwhes4mQ%3D&X-Amz-Signature=54e8073e8cb805cc8236185ceb770f80cf40bf45548daa7b10200bf6064bd4e9&X-Amz-SignedHeaders=host&response-content-disposition=inline&x-id=GetObject",
  "type": "preview",
  "key": "62b6798a2945210048ee1a8b/90c00b60-f2a7-4326-a943-bd20820d403b.mp3",
  "ext": "mp3"
}


GET <Presigned Download URL>
Download File
After you've created a presigned URL via Create Presigned Download URL, a GET request is used to download the file from Fadr's file storage. This request is not made to the Fadr API, but rather to the presigned URL you received.



POST /assets
Create Asset
Create Asset is used to create an asset in Fadr's database. Assets are database objects that store information about a file on Fadr's file storage. Creating an asset allows you to use the corresponding file in subsequent tasks like stem separation.

Request
Field	Description
s3Path	The path returned to you from Request Presigned Upload Url. Must start with "tmp/"
name	Whatever you would like to name the asset.
extension	The file extension of the file that will be uploaded.
group	A group name you can use to organize your assets.
Example request body:

{
  "name": "mysong",
  "extension": "mp3",
  "group": "mysong-stems",
  "s3Path": "tmp/62b75fc47a33a800478b8695/mysongmp3-f74bc989-aae6-4581-a225-ec01efa4e741.mp3"
}
Response
Field	Description
asset	<Asset Object>
Example response body:

{
  "asset": {
    "name": "bladee - Be Nice To Me.mp3",
    "key": "62b6798a2945210048ee1a8b/bladee%20-%20Be%20Nice%20To%20Me%20mp3-3a5a558e-3e9c-4acc-b0f2-01ac6737e410.wav",
    "uploadComplete": false,
    "user": "62b6798a2945210048ee1a8b",
    "fileType": "audio/wave",
    "assetType": "upload",
    "metaData": {
      "beats": [],
      "length": 5638144,
      "sampleRate": 44100
    },
    "group": "bladee - Be Nice To Me.mp3Stems",
    "public": false,
    "listed": false,
    "library": false,
    "stems": [],
    "midi": [],
    "revoices": [],
    "tags": [],
    "deleted": false,
    "likeCount": 0,
    "recentLikeCount": 0,
    "viewCount": 0,
    "commentCount": 0,
    "previewConstantBitRate": true,
    "api": false,
    "_id": "64d3bee537567b8d289f51dd",
    "createdTimestamp": "2023-08-09T16:29:25.334Z",
    "__v": 0
  }
}


GET /assets/:_id
Get Asset By Id
Get Asset By Id is used to read an asset document from Fadr's database. Get Asset By Id is a dynamic route with the path parameters described below.

Path Parameters	Description
_id	The _id property of the asset document you wish to return.
Response
Field	Description
asset	<Asset Object>
Example response body:

{
  "asset": {
    "metaData": {
      "sourceType": "stem",
      "stemType": "instrumental",
      "tempo": 140,
      "beats": [],
      "key": "B:min",
      "length": 5638144,
      "sampleRate": 44100,
      "beatLength": 18900,
      "offset": 4054.0499999999997
    },
    "_id": "64d3c06437567b8d289f5246",
    "name": "bladee - Be Nice To Me.mp3-instrumental",
    "key": "62b6798a2945210048ee1a8b/bladee%20-%20Be%20Nice%20To%20Me%20mp3-24400e44-a502-459f-b144-0bf1ec709d19.wav-instrumental.wav",
    "previewKey": "62b6798a2945210048ee1a8b/bladee%20-%20Be%20Nice%20To%20Me%20mp3-24400e44-a502-459f-b144-0bf1ec709d19.wav-instrumental.mp3",
    "hqPreviewKey": "62b6798a2945210048ee1a8b/bladee%20-%20Be%20Nice%20To%20Me%20mp3-24400e44-a502-459f-b144-0bf1ec709d19.wav-instrumental-hq.mp3",
    "peaks": "62b6798a2945210048ee1a8b/bladee%20-%20Be%20Nice%20To%20Me%20mp3-24400e44-a502-459f-b144-0bf1ec709d19.wav-instrumental.wav_peaks.bin",
    "uploadComplete": true,
    "user": "62b6798a2945210048ee1a8b",
    "fileType": "audio/wave",
    "assetType": "stem",
    "group": "bladee - Be Nice To Me.mp3",
    "public": false,
    "listed": false,
    "library": false,
    "stems": [],
    "midi": [],
    "revoices": [],
    "tags": [],
    "deleted": false,
    "likeCount": 0,
    "recentLikeCount": 0,
    "viewCount": 0,
    "commentCount": 0,
    "previewConstantBitRate": true,
    "api": false,
    "createdTimestamp": "2023-08-09T16:35:48.490Z",
    "__v": 0,
    "likes": []
  }
}


POST /assets/analyze/stem
Create Stem Task
Cost: US$0.05 per minute of input audio.

Create Stem Task is used to ask the Fadr API to separate an audio file into stems, using one of four stemming models. Create Stem Task requires that you have already uploaded the audio file to Fadr's cloud file storage and created an asset representing it in Fadr's database. Please see Create Presigned Upload URL and Create Asset for more info.

There are four types of source separation that you can use. The POST request parameter "stemType" is used to distinguish between four options:

"main"
Fadr's primary source separation model that separates a complete song into four primary stems, vocals, bass, drums, and melodies. A fifth "instrumental" stem is created that is the sum of bass, drums, and melodies (everything except vocals). Using stemType: "main" is unique because it will also trigger at no extra cost:

Extraction of a unique MIDI file for the vocal, drums, bass, and melody stems.
Detection of the song's chord progression, represented in MIDI and CSV format
Detection of the song's Key and Tempo, which will be stored in all of the related asset's metaData fields.
"vocal-stem"
Fadr's lead/background vocal separation model that separates a vocal stem into two new stems: lead vocals and background vocals. When using stemType: "vocal-stem", make sure that the _id request parameter points to an asset with just vocals, not a complete song.

"melodic-stem"
Fadr's melodic separation model that separates a melodic stem into six new stems: piano, electric guitar, acoustic guitar, strings, wind, and other melodies. When using stemType: "melodic-stem", make sure that the _id request parameter points to an asset with just melodic instruments, not a complete song.

"drum-stem"
Fadr's drum separation model that separates a drum stem into three new stems: kick, snare, and other drums. When using stemType: "drum-stem", make sure that the _id request parameter points to an asset with just drums, not a complete song.

After making a Create Stem Task request, you will receive a quick response with a task document. The task.status.complete subfield will be false, because the task has just started. To figure out when your task is complete and your stems are ready, poll the Get Task By ID endpoint until you find that the task.status.complete subfield is true. Now, you can access your stems in two ways:

The task.output.assets subfield will be populated with the newly created stem assets.
Use Get Asset By ID on the source asset, and you will find that the asset.stems field has been populated with the _id fields of the newly created stem assets.
You can learn more about the complete stem separation workflow by example using the API Stems Tutorial.

Request
Field	Description
_id	The _id field of the asset you wish to stem.
stemType	The identifier of the source separation model you wish to use ("main", "drum-stem", "melodic-stem", or "vocal-stem")
Example request body:

{ "_id": "64cbc6799ae99b683d6b1a56", stemType: "drum-stem" }
Response
Field	Description
task	<Task Object>
msg	Deprecated field that you can ignore.
Example response body:

{
  "task": {
    "asset": "64cbc6799ae99b683d6b1a56",
    "user": "62b6798a2945210048ee1a8b",
    "type": "stemming",
    "api": true,
    "stemQuality": "premium",
    "stemNumber": 2,
    "status": {
      "msg": "Stemming",
      "progress": 10,
      "complete": false
    },
    "startDate": "2023-08-09T16:35:21.007Z",
    "output": {
      "assets": []
    },
    "_id": "64d3c04937567b8d289f523b",
    "__v": 0,
    "id": "64d3c04937567b8d289f523b"
  },
  "msg": "Subscribe to the socket to receive updates"
}


GET /tasks/:_id
Get Task By Id
Get Task By Id is used to read an task document from Fadr's database. Get Task By Id is a dynamic route with the path parameters described below.

Path Parameters	Description
_id	The _id property of the task document you wish to return.
Response
Field	Description
task	<Task Object>
Example response body:

{
  "task": {
    "asset": "64cbc6799ae99b683d6b1a56",
    "user": "62b6798a2945210048ee1a8b",
    "type": "stemming",
    "api": true,
    "stemQuality": "premium",
    "stemNumber": 2,
    "status": {
      "msg": "Stemming",
      "progress": 10,
      "complete": false
    },
    "startDate": "2023-08-09T16:35:21.007Z",
    "output": {
      "assets": []
    },
    "_id": "64d3c04937567b8d289f523b",
    "__v": 0,
    "id": "64d3c04937567b8d289f523b"
  }
}


POST /tasks
Get Tasks By Ids
Get Tasks By Ids is used to read multiple task documents from Fadr's database in one request.

Request
Field	Description
_ids	An array of strings corresponding to the _id fields of the tasks to read.
Example request body:

{ "_ids": ["64d3c04937567b8d289f523b", "64d3c04937567b8d289f523c"] }
Response
Field	Description
tasks	[<Task Objects>]
