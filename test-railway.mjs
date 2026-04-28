import https from 'node:https';

const TOKEN = '2481fc3f-7969-480a-b3bd-8da55886ad6d';
const endpoints = ['/graphql', '/api/graphql', '/v2/graphql', '/graphql/v2'];

function graphqlQuery(query, endpoint) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({ query });
    const options = {
      hostname: 'backboard.railway.app',
      path: endpoint,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, data }));
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

for (const ep of endpoints) {
  try {
    const result = await graphqlQuery('{ me { email } }', ep);
    console.log(`${ep} -> ${result.status}: ${result.data.substring(0, 300)}`);
  } catch (e) {
    console.log(`${ep} -> ERROR: ${e.message}`);
  }
}
