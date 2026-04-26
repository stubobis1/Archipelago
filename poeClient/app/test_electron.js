const electron = require("electron");
console.log("typeof electron:", typeof electron);
console.log("electron:", JSON.stringify(electron, null, 2).substring(0, 200));
console.log("electron.app:", electron.app);
console.log("keys:", Object.keys(electron || {}).slice(0, 10));
