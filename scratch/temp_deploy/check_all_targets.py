with open("/home/lv/Desktop/fast-platform-core/frontend/dist/_app/immutable/chunks/Cu6plpcm.js", "r") as f:
    content = f.read()

targets = {
    "t1": 'async function s(r){try{const u=X()?`/api/v1/notifications/${r}/read`:`/api/v1/client/notifications/${r}/read`;await U.patch(u,{});const i=t.notifications.find(c=>c.id===r);i&&(i.isRead=!0)}catch(u){console.error("Failed to mark notification as read",u)}}',
    "t2": 'async function a(r){try{await U.post("/api/v1/notifications/bulk-delete",{ids:r}),t.notifications=t.notifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to bulk delete notifications",u)}}',
    "t3": 'addPendingSignal:r=>{if(r.id&&t.notifications.some(i=>i.id===r.id))return console.debug(`[NotificationState] Skipped duplicate signal: ${r.id}`),!1;const u={id:r.id.startsWith("sse-")?r.id:`sse-${r.id}`,message:r.message,isRead:r.isRead,type:r.signal_type||r.severity,created_at:new Date().toISOString(),payload:r.payload};if(t.notifications=[u,...t.notifications].slice(0,200),r.severity==="ACTION"||r.severity==="CRITICAL")try{J.playNotificationPing()}catch(i){console.warn("[NotificationState] playNotificationPing failed:",i)}return!0}',
    "t4": 'restoreNotifications:async r=>{try{await U.post("/api/v1/notifications/trash/restore",{ids:r}),t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id)),await e(!0)}catch(u){console.error("Failed to restore notifications",u)}}',
    "t5": 'hardDeleteNotifications:async r=>{try{await U.post("/api/v1/notifications/trash/hard-delete",{ids:r}),r.length===0?t.trashNotifications=[]:t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to hard delete notifications",u)}}',
    "t6": 'if(r){const p=new Set(c.map(T=>T.id)),m=t.notifications.filter(T=>!p.has(T.id)&&T.id.startsWith("sse-"));t.notifications=[...m,...c].slice(0,200)}else{const p=new Set(t.notifications.map(T=>T.id)),m=c.filter(T=>!p.has(T.id));t.notifications=[...t.notifications,...m]}',
    "t7": 'else{const f=new Set(t.trashNotifications.map(d=>d.id)),l=T.filter(d=>!f.has(d.id));t.trashNotifications=[...t.trashNotifications,...l]}'
}

for name, target in targets.items():
    print(f"{name} in content: {target in content}")
