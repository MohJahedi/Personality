/** Synthetic UI transport only. No sessions or credentials; never imported by production. */
(() => {
 const permissions=["users.manage", "roles.manage", "years.manage", "academics.manage", "academics.read", "students.read.all", "students.read.assigned", "students.read.linked", "students.read.self", "students.write", "finance.read.all", "finance.read.linked", "finance.read.self", "finance.write", "attendance.read.all", "attendance.read.assigned", "attendance.read.linked", "attendance.read.self", "attendance.write.all", "attendance.write.assigned", "backup.export"];
 const user={id:'qa-user',username:'ui-story',display_name:'مدیر نمونهٔ طراحی',roles:['system_admin'],permissions,must_change_password:false};
 const years=[{id:'y1',title:'۱۴۰۵–۱۴۰۶',starts_on:'2026-09-23',ends_on:'2027-09-22',status:'active'},{id:'y2',title:'۱۴۰۶–۱۴۰۷',starts_on:'2027-09-23',ends_on:'2028-09-22',status:'draft'}];
 const fiscal=[{id:'fy1',title:'مالی ۱۴۰۵',starts_on:'2026-03-21',ends_on:'2027-03-20',status:'active'}];
 const catalog={grades:[{id:'g1',name:'پنجم',position:5}],subjects:[{id:'sub1',name:'ریاضی'},{id:'sub2',name:'علوم'}],gradeSubjects:[{grade_id:'g1',subject_id:'sub1'},{grade_id:'g1',subject_id:'sub2'}],classes:[{id:'c1',academic_year_id:'y1',grade_id:'g1',name:'پنجم الف',capacity:30},{id:'c2',academic_year_id:'y1',grade_id:'g1',name:'پنجم ب',capacity:30}],teachers:[{id:'t1',name:'معلم نمونه'}],periods:[{id:'p1',academic_year_id:'y1',grade_id:'g1',weekday:0,number:1,starts_at:'08:00',ends_at:'08:45'},{id:'p2',academic_year_id:'y1',grade_id:'g1',weekday:0,number:2,starts_at:'09:00',ends_at:'09:45'},{id:'p3',academic_year_id:'y1',grade_id:'g1',weekday:1,number:1,starts_at:'08:00',ends_at:'08:45'}]};
 const students=[{id:'s1',name:'دانش‌آموز نمونهٔ اول',code:'S-001',guardian_name:'ولی نمونه',guardian_phone:'',class_id:'c1',grade_id:'g1',enrolled_class:'پنجم الف'},{id:'s2',name:'دانش‌آموز نمونهٔ دوم',code:'S-002',guardian_name:'ولی نمونه',guardian_phone:'',class_id:'c1',grade_id:'g1',enrolled_class:'پنجم الف'}];
 const invoices=[{id:'i1',student_id:'s1',student_name:students[0].name,title:'شهریهٔ نمونه',amount:400000000,paid:120000000,due_date:'2026-12-01',academic_year_id:'y1'}];
 const balances={balances:[{id:'s1',name:students[0].name,code:'S-001',invoice_id:'i1',title:'شهریهٔ نمونه',amount:400000000,paid:120000000,remaining:280000000,opening_amount:0}],total:280000000,openingSnapshot:0};
 const query=new URLSearchParams(location.search); let preferences={font:'vazirmatn',size:query.get('size')||'normal',theme:'sky',accent:''};
 const roles=[{id:'system_admin',name:'ادمین سیستم',permissions,built_in:1},{id:'manager',name:'مدیر',permissions:permissions.filter(p=>!['users.manage','roles.manage'].includes(p)),built_in:1},{id:'accountant',name:'حسابدار',permissions:['finance.write','finance.read.all','students.read.all'],built_in:1},{id:'teacher',name:'معلم',permissions:['academics.read','students.read.assigned'],built_in:1},{id:'student',name:'دانش‌آموز',permissions:['students.read.self'],built_in:1},{id:'parent',name:'ولی',permissions:['students.read.linked'],built_in:1}];
 const users=[{id:'qa-user',username:'ui-story',display_name:user.display_name,status:'active',roles:['system_admin'],studentIds:[],classIds:[]}];
 let timetable=[{id:'tt1',class_id:'c1',period_id:'p1',subject_id:'sub1',teacher_id:'t1',weekday:0,number:1,starts_at:'08:00',ends_at:'08:45',class_name:'پنجم الف',subject_name:'ریاضی',teacher_name:'معلم نمونه'}];
 let attendance=[];
 const nativeFetch=window.fetch.bind(window);
 window.fetch=async(input,options={})=>{
  const url=new URL(String(input),location.origin);
  if(!url.pathname.startsWith('/api/v1/'))return nativeFetch(input,options);
  const path=url.pathname.slice('/api/v1'.length);const payload=options.body?JSON.parse(options.body):null;
  let data;
  if(payload){
   if(path==='/preferences')preferences=payload;
   if(path==='/profile')user.display_name=payload.name;
   if(path==='/academics'&&payload.kind==='grade')catalog.grades.push({id:crypto.randomUUID(),name:payload.name,position:payload.position});
   if(path==='/years')years.push({id:crypto.randomUUID(),...payload});
   if(path==='/users')users.push({id:crypto.randomUUID(),username:payload.username,display_name:payload.name,status:'active',roles:payload.roles,studentIds:payload.studentIds,classIds:payload.classIds});
   if(path==='/roles')roles.push({id:crypto.randomUUID(),name:payload.name,permissions:payload.permissions,built_in:0});
   if(path==='/attendance')attendance=[{student_id:payload.studentId,status:payload.status}];
   if(path==='/timetable/remove')timetable=timetable.filter(t=>t.id!==payload.id);
   data={ok:true,id:'qa-result',copied:{students:2,teachers:1,parents:1,classes:2}};
  }else{
   const map={
    '/context':{setupRequired:false,setupProtected:false,user,preferences},
    '/years':{academicYears:years,fiscalYears:fiscal},'/academics':catalog,'/students':{students},'/balances':balances,
    '/finance':{students,invoices,receipts:[{id:'r1',invoice_id:'i1',student_name:students[0].name,invoice_title:'شهریه نمونه',amount:120000000,reference:'ساختگی',created_at:'2026-11-03T08:00:00Z'}],journals:[{id:'j1',description:'مطالبه شهریه نمونه',student_name:students[0].name,debit_account:'1301',credit_account:'2101',amount:400000000,fiscal_year_id:'fy1',posted_on:'2026-11-03'}]},
    '/profile':{name:user.display_name,username:'ui-story',first_name:'نام نمونه',last_name:'آزمون',phone:'',email:''},
    '/roles':{roles,permissions:{"users.manage": "مدیریت کاربران و انتصاب نقش", "roles.manage": "تعریف و ویرایش نقش", "years.manage": "مدیریت و کپی سال تحصیلی", "academics.manage": "مدیریت پایه، درس، کلاس و برنامه", "academics.read": "مشاهدهٔ ساختار آموزشی", "students.read.all": "مشاهدهٔ همهٔ پرونده‌ها", "students.read.assigned": "مشاهدهٔ کلاس‌های تخصیص‌یافته", "students.read.linked": "مشاهدهٔ فرزندان مرتبط", "students.read.self": "مشاهدهٔ پروندهٔ خود", "students.write": "ثبت و انتساب پرونده", "finance.read.all": "مشاهدهٔ مالی همهٔ دانش‌آموزان", "finance.read.linked": "مشاهدهٔ مالی فرزندان مرتبط", "finance.read.self": "مشاهدهٔ مالی خود", "finance.write": "ثبت شهریه، دریافت و انتقال مانده", "attendance.read.all": "مشاهدهٔ همهٔ حضورها", "attendance.read.assigned": "مشاهدهٔ حضور کلاس‌های خود", "attendance.read.linked": "مشاهدهٔ حضور فرزندان", "attendance.read.self": "مشاهدهٔ حضور خود", "attendance.write.all": "ثبت حضور همهٔ کلاس‌ها", "attendance.write.assigned": "ثبت حضور کلاس‌های تخصیص‌یافته", "backup.export": "دریافت پشتیبان کامل مدرسه"}},'/users':{users},'/timetable':{timetable},'/attendance':{students,attendance},
    '/years/copy-preview':{counts:{students:2,teachers:1,parents:1,classes:2},version:'qa-copy',notes:['این پیش‌نمایش رابط با API ساختگی است؛ آزمون سرور جدا انجام می‌شود.']},
    '/years/carry-preview':{version:'qa-carry',amount:280000000,studentCount:1,claims:[{invoice_id:'i1',student_id:'s1',student_name:students[0].name,title:'شهریه نمونه',remaining:280000000}]}
   };data=map[path];
  }
  return new Response(JSON.stringify(data??{error:'UI fixture has no route: '+path}),{status:data?200:404,headers:{'Content-Type':'application/json'}});
 };
})();