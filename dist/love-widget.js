// Love Notes — run once in Scriptable to pair, then select this script in a medium widget.
const origin='https://notes.example.com';
const key='love-notes-widget-token';
let token=Keychain.contains(key)?Keychain.get(key):null;
if(!config.runsInWidget){
  const menu=new Alert();menu.title='Love Notes';menu.message=token?'Your daily-note widget is connected. Reconnect to use a new pairing code.':'Create a widget code in Love Notes, then connect it here.';
  menu.addAction(token?'Reconnect widget':'Connect widget');menu.addCancelAction('Keep current connection');
  if(await menu.presentAlert()===0){const dialog=new Alert();dialog.title='Your widget code';dialog.message='Enter the code from the Love Notes website.';dialog.addTextField('12-character code');dialog.addAction('Connect');dialog.addCancelAction('Cancel');
    if(await dialog.presentAlert()===0){try{const req=new Request(origin+'/api/widget-connect');req.method='POST';req.headers={'Content-Type':'application/json'};req.body=JSON.stringify({code:dialog.textFieldValue(0).trim()});const result=await req.loadJSON();if(!result.token)throw new Error(result.error||'Couldn’t connect.');token=result.token;Keychain.set(key,token);}catch(e){const error=new Alert();error.title='A little connection trouble';error.message=e.message;error.addAction('OK');await error.presentAlert();}}
  }
}
let note=null,message='Run this script in Scriptable to connect your daily note.';
if(token){try{const req=new Request(origin+'/api/widget-today');req.headers={'Authorization':'Bearer '+token};req.timeoutInterval=15;const data=await req.loadJSON();if(!data.note)throw new Error(data.error||'Open the app to reconnect.');note=data;}catch(e){message='Open Love Notes to reconnect or check your connection.';}}
const widget=new ListWidget();widget.backgroundColor=new Color('#ffe0bd');widget.setPadding(16,18,16,18);widget.url=origin+'/?app=1';
const top=widget.addText(note?'A little love · '+note.date:'Love Notes');top.font=Font.semiboldSystemFont(12);top.textColor=new Color('#79573e');widget.addSpacer(10);
const text=widget.addText(note?note.note.text:message);text.font=Font.semiboldRoundedSystemFont(17);text.textColor=new Color('#60422d');text.minimumScaleFactor=.65;text.lineLimit=6;widget.addSpacer();
const sign=widget.addText('always your teammate. ♡');sign.font=Font.italicSystemFont(12);sign.textColor=new Color('#a84b21');widget.refreshAfterDate=new Date(Date.now()+30*60*1000);Script.setWidget(widget);if(!config.runsInWidget)await widget.presentMedium();Script.complete();
