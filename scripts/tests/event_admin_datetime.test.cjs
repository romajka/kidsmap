const test=require('node:test'), assert=require('node:assert/strict'), fs=require('node:fs'), vm=require('node:vm');
function mount(labels, startDate, endDate) {
 const summary={dataset:labels,textContent:'',classList:{toggle(){},remove(){}}};
 const input=date=>({dataset:{},_flatpickr:{selectedDates:date?[date]:[],set(){}},addEventListener(){},closest:()=>({dataset:{}})});
 const start=input(startDate),end=input(endDate);
 vm.runInNewContext(fs.readFileSync('static/admin/js/kidsmap_event_datetime.js','utf8'),{document:{readyState:'complete',querySelector:selector=>selector.includes('="start"')?start:selector.includes('="end"')?end:summary}});
 return summary.textContent;
}
const labels={durationDay:'gün',durationHour:'saat',durationMinute:'dəq.',durationLabel:'Müddət',durationEmpty:'Vaxtı seçin',durationInvalid:'Bitmə vaxtı səhvdir'};
test('event duration uses injected locale labels',()=>assert.equal(mount(labels,new Date('2026-11-01T10:00:00Z'),new Date('2026-11-02T12:05:00Z')),'Müddət: 1 gün 2 saat 5 dəq.'));
test('event duration uses injected empty and invalid messages',()=>{
 assert.equal(mount(labels), 'Vaxtı seçin');
 assert.equal(mount(labels,new Date('2026-11-01T10:00:00Z'),new Date('2026-11-01T09:00:00Z')),'Bitmə vaxtı səhvdir');
});
