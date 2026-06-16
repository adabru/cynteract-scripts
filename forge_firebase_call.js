window.callFn = async (name, data = {}) => {
  const key = Object.keys(localStorage).find(k => k.startsWith('firebase:authUser:'));
  const token = JSON.parse(localStorage.getItem(key)).stsTokenManager.accessToken;
    console.log(token)
  const res = await fetch(
    `https://us-central1-cynteract-test.cloudfunctions.net/${name}`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data }),
    },
  );
  return res.json();
};

// then:
// testing, test01@cynteract.com
await callFn('getUserEmail', { userId: "j3K0yFMSXHWtKb9L1yyOp69Kh883" });
// await callFn('logoutUser');
// production
// await callFn('getUserEmail', { userId: "bSBVKHdsTFOcK1B8XBxExox66JJ3" });