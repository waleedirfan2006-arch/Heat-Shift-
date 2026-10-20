// Software parity check on real validation feature rows; no fitting or tuning.
const fs=require('fs'),zlib=require('zlib'),assert=require('assert');
const inference=require('./model.js');
const m=JSON.parse(zlib.gunzipSync(fs.readFileSync(__dirname+'/station_weather_model.json.gz')));
const vectors=JSON.parse(process.argv[2].endsWith('.gz')?zlib.gunzipSync(fs.readFileSync(process.argv[2])).toString('utf8'):fs.readFileSync(process.argv[2],'utf8'));
let max=0;
for(const vector of vectors){const p=inference.predictResidual(vector.row,m);const error=Math.abs(p-vector.expected_residual);max=Math.max(max,error);assert(error<1e-10,'Browser/Python prediction mismatch');if(vector.expected_prediction!==undefined)assert(Math.abs(vector.row.current_c+(m.residual_weight??1)*p-vector.expected_prediction)<1e-10,'Full forecast precision mismatch');}
console.log(`New weather model matches Python on ${vectors.length} real validation feature rows; max difference ${max}.`);
