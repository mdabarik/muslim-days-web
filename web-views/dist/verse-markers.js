let frameReady=false;
export async function loadVerseFrame(){
 try{const faces=await document.fonts.load('24px "Verse Frame"');frameReady=faces.length>0}catch{frameReady=false}
}
export function verseNumber(text){
 const node=document.createElement('span');node.className='verse-number';node.setAttribute('aria-label','আয়াত '+text);
 if(frameReady){node.classList.add('decorated-verse');const frame=document.createElement('span');frame.className='verse-frame';frame.textContent='\ue200';frame.setAttribute('aria-hidden','true');node.append(frame)}
 const digits=document.createElement('span');digits.className='verse-digits';digits.textContent=text;digits.lang='bn';digits.dir='ltr';node.dataset.digits=String([...text].length);node.append(digits);return node;
}
