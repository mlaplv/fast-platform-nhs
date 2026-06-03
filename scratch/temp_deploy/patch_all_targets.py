filepath = "/home/lv/Desktop/fast-platform-core/frontend/dist/_app/immutable/chunks/Cu6plpcm.js"

with open(filepath, "r") as f:
    content = f.read()

# 1. Patch markNotificationAsRead (s)
t1 = 'async function s(r){try{const u=X()?`/api/v1/notifications/${r}/read`:`/api/v1/client/notifications/${r}/read`;await U.patch(u,{});const i=t.notifications.find(c=>c.id===r);i&&(i.isRead=!0)}catch(u){console.error("Failed to mark notification as read",u)}}'
r1 = 'async function s(r){try{const o=r.startsWith("sse-")?r.slice(4):r,u=X()?`/api/v1/notifications/${o}/read`:`/api/v1/client/notifications/${o}/read`;await U.patch(u,{});const i=t.notifications.find(c=>c.id===r);i&&(i.isRead=!0)}catch(u){console.error("Failed to mark notification as read",u)}}'

if t1 in content:
    content = content.replace(t1, r1)
    print("Success: Patched t1 (markNotificationAsRead)")
else:
    print("Error: Target 1 not found")

# 2. Patch bulkDeleteNotifications (a)
t2 = 'async function a(r){try{await U.post("/api/v1/notifications/bulk-delete",{ids:r}),t.notifications=t.notifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to bulk delete notifications",u)}}'
r2 = 'async function a(r){try{const o=r.map(d=>d.startsWith("sse-")?d.slice(4):d);await U.post("/api/v1/notifications/bulk-delete",{ids:o}),t.notifications=t.notifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to bulk delete notifications",u)}}'

if t2 in content:
    content = content.replace(t2, r2)
    print("Success: Patched t2 (bulkDeleteNotifications)")
else:
    print("Error: Target 2 not found")

# 3. Patch addPendingSignal
t3 = 'addPendingSignal:r=>{if(r.id&&t.notifications.some(i=>i.id===r.id))return console.debug(`[NotificationState] Skipped duplicate signal: ${r.id}`),!1;const u={id:r.id.startsWith("sse-")?r.id:`sse-${r.id}`,message:r.message,isRead:r.isRead,type:r.signal_type||r.severity,created_at:new Date().toISOString(),payload:r.payload};if(t.notifications=[u,...t.notifications].slice(0,200),r.severity==="ACTION"||r.severity==="CRITICAL")try{J.playNotificationPing()}catch(i){console.warn("[NotificationState] playNotificationPing failed:",i)}return!0}'
r3 = 'addPendingSignal:r=>{const o=r.id.startsWith("sse-")?r.id:`sse-${r.id}`,e=r.id.startsWith("sse-")?r.id.slice(4):r.id;if(r.id&&t.notifications.some(i=>{const c=i.id.startsWith("sse-")?i.id.slice(4):i.id;return i.id===r.id||c===e||i.id===o}))return console.debug(`[NotificationState] Skipped duplicate signal: ${r.id}`),!1;const u={id:o,message:r.message,isRead:r.isRead,type:r.signal_type||r.severity,created_at:new Date().toISOString(),payload:r.payload};if(t.notifications=[u,...t.notifications].slice(0,200),r.severity==="ACTION"||r.severity==="CRITICAL")try{J.playNotificationPing()}catch(i){console.warn("[NotificationState] playNotificationPing failed:",i)}return!0}'

if t3 in content:
    content = content.replace(t3, r3)
    print("Success: Patched t3 (addPendingSignal)")
else:
    print("Error: Target 3 not found")

# 4. Patch restoreNotifications
t4 = 'restoreNotifications:async r=>{try{await U.post("/api/v1/notifications/trash/restore",{ids:r}),t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id)),await e(!0)}catch(u){console.error("Failed to restore notifications",u)}}'
r4 = 'restoreNotifications:async r=>{try{const o=r.map(d=>d.startsWith("sse-")?d.slice(4):d);await U.post("/api/v1/notifications/trash/restore",{ids:o}),t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id)),await e(!0)}catch(u){console.error("Failed to restore notifications",u)}}'

if t4 in content:
    content = content.replace(t4, r4)
    print("Success: Patched t4 (restoreNotifications)")
else:
    print("Error: Target 4 not found")

# 5. Patch hardDeleteNotifications
t5 = 'hardDeleteNotifications:async r=>{try{await U.post("/api/v1/notifications/trash/hard-delete",{ids:r}),r.length===0?t.trashNotifications=[]:t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to hard delete notifications",u)}}'
r5 = 'hardDeleteNotifications:async r=>{try{const o=r.map(d=>d.startsWith("sse-")?d.slice(4):d);await U.post("/api/v1/notifications/trash/hard-delete",{ids:o}),r.length===0?t.trashNotifications=[]:t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to hard delete notifications",u)}}'

if t5 in content:
    content = content.replace(t5, r5)
    print("Success: Patched t5 (hardDeleteNotifications)")
else:
    print("Error: Target 5 not found")

# 6. Patch fetchNotifications merge
t6 = 'if(r){const p=new Set(c.map(T=>T.id)),m=t.notifications.filter(T=>!p.has(T.id)&&T.id.startsWith("sse-"));t.notifications=[...m,...c].slice(0,200)}else{const p=new Set(t.notifications.map(T=>T.id)),m=c.filter(T=>!p.has(T.id));t.notifications=[...t.notifications,...m]}'
r6 = 'if(r){const p=new Set(c.map(T=>T.id.startsWith("sse-")?T.id.slice(4):T.id)),m=t.notifications.filter(T=>{const g=T.id.startsWith("sse-")?T.id.slice(4):T.id;return!p.has(g)&&T.id.startsWith("sse-")});t.notifications=[...m,...c].slice(0,200)}else{const p=new Set(t.notifications.map(T=>T.id.startsWith("sse-")?T.id.slice(4):T.id)),m=c.filter(T=>{const g=T.id.startsWith("sse-")?T.id.slice(4):T.id;return!p.has(g)});t.notifications=[...t.notifications,...m]}'

if t6 in content:
    content = content.replace(t6, r6)
    print("Success: Patched t6 (fetchNotifications merge)")
else:
    print("Error: Target 6 not found")

# 7. Patch fetchTrashNotifications pagination merge
t7 = 'else{const f=new Set(t.trashNotifications.map(d=>d.id)),l=T.filter(d=>!f.has(d.id));t.trashNotifications=[...t.trashNotifications,...l]}'
r7 = 'else{const f=new Set(t.trashNotifications.map(d=>d.id.startsWith("sse-")?d.id.slice(4):d.id)),l=T.filter(d=>{const g=d.id.startsWith("sse-")?d.id.slice(4):d.id;return!f.has(g)});t.trashNotifications=[...t.trashNotifications,...l]}'

if t7 in content:
    content = content.replace(t7, r7)
    print("Success: Patched t7 (fetchTrashNotifications pagination merge)")
else:
    print("Error: Target 7 not found")

with open(filepath, "w") as f:
    f.write(content)

print("Local file patch complete!")
