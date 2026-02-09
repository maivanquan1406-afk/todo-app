/**
 * reminders.js - Setup client-side reminders for tasks
 * Nhắc nhở người dùng về các công việc sắp tới
 */

/**
 * Setup reminders for todos with due dates
 */
function setupReminders() {
  todos.forEach(t => {
    if (!t.due_date) return;
    const due = new Date(t.due_date);
    const now = new Date();
    const ms = due - now;
    if (ms > 0 && ms < 1000*60*60*24*7) { // only set reminders within next 7 days
      setTimeout(()=>{
        alert('Nhắc: ' + t.title + '\n' + (t.description||''));
      }, ms);
    }
  });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', setupReminders);
} else {
  setupReminders();
}
