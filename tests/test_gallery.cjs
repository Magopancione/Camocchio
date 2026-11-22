const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');let source=fs.readFileSync(path.join(__dirname,'../src/app.py'),'utf8');let code=source.split('<script>')[1].split('</script>')[0];
let helper=code.slice(code.indexOf('function normalizedPageSize'),code.indexOf('let selected=null;'));
let els={gallery_day_only:{checked:false},day:{value:'2026-11-22'},library_page_size:{value:'12'}};
let ctx={document:{getElementById:id=>els[id]},libraryItems:[{name:'V380_2026-11-22_01-00-00',date:'22-11-2026'},{name:'V380_2026-11-21_01-00-00',date:'21-11-2026'}]};vm.createContext(ctx);vm.runInContext(helper,ctx);
assert.equal(ctx.normalizedPageSize(8),12);assert.equal(ctx.normalizedPageSize(18),18);assert.equal(ctx.normalizedPageSize('all'),'all');
assert.equal(ctx.filteredLibrary().length,2);els.gallery_day_only.checked=true;assert.equal(ctx.filteredLibrary().length,1);els.library_page_size.value='all';assert.equal(ctx.galleryPageSize(),1);els.day.value='2026-11-20';assert.equal(ctx.filteredLibrary().length,0);assert.equal(ctx.galleryPageSize(),1);
console.log('PASS: day filter, empty day, All, legacy page-size normalization');
