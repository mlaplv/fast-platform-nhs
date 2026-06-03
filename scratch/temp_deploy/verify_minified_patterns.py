with open("/home/lv/Desktop/fast-platform-core/frontend/dist/_app/immutable/chunks/Cu6plpcm.js", "r") as f:
    content = f.read()

t6 = 'if(r){const p=new Set(c.map(T=>T.id)),m=t.notifications.filter(T=>!p.has(T.id)&&T.id.startsWith("sse-"));t.notifications=[...m,...c].slice(0,200)}else{const p=new Set(t.notifications.map(T=>T.id)),m=c.filter(T=>!p.has(T.id));t.notifications=[...t.notifications,...m]}'
t7 = 'else{const f=new Set(t.trashNotifications.map(d=>d.id)),l=T.filter(d=>!f.has(d.id));t.trashNotifications=[...t.trashNotifications,...l]}'

print("t6 in content:", t6 in content)
print("t7 in content:", t7 in content)
