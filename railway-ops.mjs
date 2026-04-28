import https from 'node:https';

const TOKEN = '2481fc3f-7969-480a-b3bd-8da55886ad6d';

async function gql(query, variables = {}) {
  const body = JSON.stringify({ query, variables });
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'backboard.railway.app',
      path: '/graphql/v2',
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
      res.on('end', () => resolve(JSON.parse(data)));
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  // Try to find project by slug using different query patterns
  // Railway might support a projectBySlug query
  const queries = [
    `{ projectBySlug(projectSlug: "api-relay") { id name } }`,
    `{ projectByName(name: "api-relay") { id name } }`,
    `{ projectById(id: "api-relay") { id name } }`,
    // Check me.workspaces[0].projects with more pagination
    `{ me { workspaces { id name projects(first: 100) { edges { node { id name } } } } } }`,
  ];
  for (const q of queries) {
    const r = await gql(q);
    console.log(`\nQuery: ${q.substring(0, 60)}...`);
    console.log(JSON.stringify(r, null, 2).substring(0, 300));
  }
}

main().catch(console.error);
