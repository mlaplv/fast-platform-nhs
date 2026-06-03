with open("scratch/temp_deploy/Cu6plpcm.js", "r") as f:
    content = f.read()

# 1. Patch markNotificationAsRead (s)
t1 = 'async function s(r){try{const u=X()?`/api/v1/notifications/${r}/read`:`/api/v1/client/notifications/${r}/read`;await U.patch(u,{});const i=t.notifications.find(c=>c.id===r);i&&(i.isRead=!0)}catch(u){console.error("Failed to mark notification as read",u)}}'
r1 = 'async function s(r){try{const o=r.startsWith("sse-")?r.slice(4):r,u=X()?`/api/v1/notifications/${o}/read`:`/api/v1/client/notifications/${o}/read`;await U.patch(u,{});const i=t.notifications.find(c=>c.id===r);i&&(i.isRead=!0)}catch(u){console.error("Failed to mark notification as read",u)}}'

if t1 in content:
    content = content.replace(t1, r1)
    print("Success: Patched markNotificationAsRead")
else:
    print("Error: Target 1 not found")

# 2. Patch bulkDeleteNotifications (a)
t2 = 'async function a(r){try{await U.post("/api/v1/notifications/bulk-delete",{ids:r}),t.notifications=t.notifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to bulk delete notifications",u)}}'
r2 = 'async function a(r){try{const o=r.map(d=>d.startsWith("sse-")?d.slice(4):d);await U.post("/api/v1/notifications/bulk-delete",{ids:o}),t.notifications=t.notifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to bulk delete notifications",u)}}'

if t2 in content:
    content = content.replace(t2, r2)
    print("Success: Patched bulkDeleteNotifications")
else:
    print("Error: Target 2 not found")

# 3. Patch addPendingSignal
t3 = 'addPendingSignal:r=>{if(r.id&&t.notifications.some(i=>i.id===r.id))return console.debug(`[NotificationState] Skipped duplicate signal: ${r.id}`),!1;const u={id:r.id.startsWith("sse-")?r.id:`sse-${r.id}`,message:r.message,isRead:r.isRead,type:r.signal_type||r.severity,created_at:new Date().toISOString(),payload:r.payload};if(t.notifications=[u,...t.notifications].slice(0,200),r.severity==="ACTION"||r.severity==="CRITICAL")try{J.playNotificationPing()}catch(i){console.warn("[NotificationState] playNotificationPing failed:",i)}return!0}'
r3 = 'addPendingSignal:r=>{const o=r.id.startsWith("sse-")?r.id:`sse-${r.id}`,e=r.id.startsWith("sse-")?r.id.slice(4):r.id;if(r.id&&t.notifications.some(i=>{const c=i.id.startsWith("sse-")?i.id.slice(4):i.id;return i.id===r.id||c===e||i.id===o}))return console.debug(`[NotificationState] Skipped duplicate signal: ${r.id}`),!1;const u={id:o,message:r.message,isRead:r.isRead,type:r.signal_type||r.severity,created_at:new Date().toISOString(),payload:r.payload};if(t.notifications=[u,...t.notifications].slice(0,200),r.severity==="ACTION"||r.severity==="CRITICAL")try{J.playNotificationPing()}catch(i){console.warn("[NotificationState] playNotificationPing failed:",i)}return!0}'

if t3 in content:
    content = content.replace(t3, r3)
    print("Success: Patched addPendingSignal")
else:
    print("Error: Target 3 not found")

# 4. Patch restoreNotifications
t4 = 'restoreNotifications:async r=>{try{await U.post("/api/v1/notifications/trash/restore",{ids:r}),t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id)),await e(!0)}catch(u){console.error("Failed to restore notifications",u)}}'
r4 = 'restoreNotifications:async r=>{try{const o=r.map(d=>d.startsWith("sse-")?d.slice(4):d);await U.post("/api/v1/notifications/trash/restore",{ids:o}),t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id)),await e(!0)}catch(u){console.error("Failed to restore notifications",u)}}'

if t4 in content:
    content = content.replace(t4, r4)
    print("Success: Patched restoreNotifications")
else:
    print("Error: Target 4 not found")

# 5. Patch hardDeleteNotifications
t5 = 'hardDeleteNotifications:async r=>{try{await U.post("/api/v1/notifications/trash/hard-delete",{ids:r}),r.length===0?t.trashNotifications=[]:t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to hard delete notifications",u)}}'
r5 = 'hardDeleteNotifications:async r=>{try{const o=r.map(d=>d.startsWith("sse-")?d.slice(4):d);await U.post("/api/v1/notifications/trash/hard-delete",{ids:o}),r.length===0?t.trashNotifications=[]:t.trashNotifications=t.trashNotifications.filter(u=>!r.includes(u.id))}catch(u){console.error("Failed to hard delete notifications",u)}}'

if t5 in content:
    content = content.replace(t5, r5)
    print("Success: Patched hardDeleteNotifications")
else:
    print("Error: Target 5 not found")

with open("scratch/temp_deploy/Cu6plpcm.js", "w") as f:
    f.write(content)
print("File written.")
