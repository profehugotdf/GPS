// Dos funciones con el mismo nombre en index.html: la segunda pisa a la primera sin aviso (ya pasó con chainLines).
const fs=require('fs');const src=fs.readFileSync('index.html','utf8');
const seen=new Map(),dups=[];let line=1;
for(const l of src.split('\n')){const m=l.match(/^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(/);if(m){if(seen.has(m[1]))dups.push(`${m[1]} (líneas ${seen.get(m[1])} y ${line})`);else seen.set(m[1],line);}line++;}
console.log((dups.length?'FALLA ':'OK    ')+'funciones repetidas: '+(dups.join(', ')||'ninguna')+` (${seen.size} funciones)`);
