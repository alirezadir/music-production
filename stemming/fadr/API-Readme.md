https://fadr.com/docs/api-stems-tutorial

Steps
01
Authenticate
Follow the authentication guide to learn how to authenticate your requests.

02
Upload your audio file
The first step is uploading your source audio file. The Fadr API uses presigned URLs to provide temporary permissions to Fadr's file storage. First, make a POST request to the Create Presigned Upload URL endpoint. Then, use a PUT request to the presigned URL you create to upload your file. Make sure you specify the MIME type of the file you are uploading via the Content-Type header on the PUT request - learn more.

03
Create an asset for your file
Once you've uploaded your audio file, create an asset in Fadr's database to describe your file using a POST request to the Create Asset endpoint. From then on, you will only use the asset in communication with the Fadr API.

04
Create a stem task for your asset
Now you're ready to stem your audio. Create a stem task for your asset by making a POST request to the Create Stem Task endpoint. You will quickly receive a response with a task, and various Fadr AI models included with stemming will start running.

The stem task includes:

Separation into the 5 primary stems (vocals, drums, bass, melodies and instrumental)
Midi of the vocals, drums, and bass stems
Midi representing the chord progression
Key and tempo detection
The first model to finish is stems, and then midi, key and tempo. Stems usually take around 10-20 seconds, and the remainder usually takes another 10-20 seconds.

05
Poll for stem task status updates (stems, midi, etc.)
As each model finishes, the task will update in Fadr's database. Poll the Get Task By Id endpoint using GET requests at regular intervals to get the latest task document and watch for status updates. We recommend polling at 5 second intervals.

If you just need stems, you can move on to steps 5 and 6 to download the stems before the midi is done.

06
Get the new assets
As the task status changes, you will also notice changes to the task's asset. For example, when stems are done separating, the asset will have a property callled "stems". This property is an array of strings corresponding to the id properties of the new stem assets that were created during the stem task. Similarly, when midi is done, you will find a "midi" property, which is an array of strings corresponding to id properties of the new midi assets that were created during the stem task.

07
Download your new files
For any _id found in the source asset's "stems" or "midi" arrays, you can use a GET request to the Create Presigned Download URL endpoint. Make a GET request to the URL that is returned to download the asset's corresponding file.

const fs = require('fs');
const axios = require('axios');
const { setTimeout } = require("timers/promises");

const songPath = './song.mp3';
const apiKey = "";
const url = "https://api.fadr.com";

const headers = {
  Authorization: `Bearer ${apiKey}`
}

async function stemSong(path, outPath) {
  const file = fs.readFileSync(songPath)
  // const file = new LocalFileData(songPath)
  
  // console.log(file);
  
  console.log('Getting upload URL');
  
  let response =  await axios.post(`${url}/assets/upload2`, {
    name: "song.mp3",
    extension: "mp3",
  }, {
    headers
  })
  
  const { s3Path } = response.data;

  console.log('Uploading file to Signed URL');
  
  response = await axios.put(response.data.url, file, {
    "Content-Type": 'audio/mp3'
  });

  console.log('Creating asset');

  response = await axios.post(`${url}/assets`, {
    name: "song.mp3",
    extension: "mp3",
    group: "song.mp3-group",
    s3Path: s3Path
  }, { headers });

  const { asset } = response.data;

  console.log('Starting Stem Task');

  response = await axios.post(`${url}/assets/analyze/stem`, {
    _id: asset._id
  }, { headers });

  let { task } = response.data;

  console.log('Polling for partial task completion (awaiting stems).')

  while (!task.asset.stems?.length) {
    console.log('Waiting 5 seconds...');
    await setTimeout(5000);
    response = await axios.post(`${url}/tasks/query`, {
      _ids: [task._id]
    }, { headers });
    task = response.data.tasks[0];
  }
  console.log('Task Complete');

  console.log('Getting all stems to find drums');
  let responses = await Promise.all(task.asset.stems.map((asset_id) => axios.get(`${url}/assets/${asset_id}`, { headers })));

  let stemAssets = responses.map((response) => response.data.asset);
  let drumAsset = stemAssets.find((asset) => asset.metaData.stemType === 'drums');

  response = await axios.post(`${url}/assets/analyze/stem`, {
    _id: drumAsset._id,
    stemType: "drum-stem"
  }, { headers });

  task = response.data.task;

  while (!task.asset.stems?.length) {
    console.log('Waiting 5 seconds...');
    await setTimeout(5000);
    response = await axios.post(`${url}/tasks/query`, {
      _ids: [task._id]
    }, { headers });
    console.log(response.data.tasks)
    task = response.data.tasks[0];
  }
  console.log('Task Complete');

  console.log('Getting all stems to find kick');
  responses = await Promise.all(task.asset.stems.map((asset_id) => axios.get(`${url}/assets/${asset_id}`, { headers })));
  stemAssets = responses.map((response) => response.data.asset);
  kickAsset = stemAssets.find((asset) => asset.metaData.stemType === 'kick');

  console.log('Getting download url for kick');
  response = await axios.get(`${url}/assets/download/${kickAsset._id}/hq`, { headers });
  const downloadUrl = response.data.url;
  
  console.log('Downloading kick');
  response = await axios.get(downloadUrl, { responseType: "stream" });
  const writer = fs.createWriteStream(outPath);
  response.data.pipe(writer);
}

try {
  stemSong(songPath, "out.mp3");
} catch (err) {
  console.log(err);
}