/**
 * tasks.js - Task CRUD operations
 * Xử lý thêm, hoàn thành, xóa công việc
 */

/**
 * Handle form submission with AJAX
 */
function initAddTodoForm() {
  const addTodoForm = document.getElementById('addTodoForm');
  if (!addTodoForm) return;

  addTodoForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(addTodoForm);
    
    // Add success message immediately
    const cards = document.querySelectorAll('.card');
    let card = null;
    
    for (let c of cards) {
      const header = c.querySelector('.card-header');
      if (header && header.classList.contains('bg-success')) {
        card = c;
        break;
      }
    }
    
    if (card) {
      const alertDiv = document.createElement('div');
      alertDiv.className = 'alert alert-success alert-dismissible fade show';
      alertDiv.innerHTML = `
        <i class="bi bi-check-circle"></i> Công việc đã được thêm! Đang cập nhật...
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      `;
      card.insertBefore(alertDiv, card.firstChild);
    }
    
    try {
      const response = await fetch('/dashboard/todos', {
        method: 'POST',
        body: formData
      });
      
      // Reload page after 500ms regardless of response
      setTimeout(() => {
        location.reload();
      }, 500);
      
    } catch (error) {
      console.error('Error:', error);
      // Still reload on error
      setTimeout(() => {
        location.reload();
      }, 500);
    }
  });
}

/**
 * Handle complete button clicks
 */
function initCompleteButtons() {
  document.querySelectorAll('.complete-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const todoId = btn.getAttribute('data-todo-id');
      
      try {
        const response = await fetch(`/dashboard/todos/${todoId}/complete`, {
          method: 'POST'
        });
        
        // Reload page after 300ms
        setTimeout(() => {
          location.reload();
        }, 300);
      } catch (error) {
        console.error('Error:', error);
        alert('Có lỗi xảy ra');
      }
    });
  });
}

/**
 * Handle delete button clicks
 */
function initDeleteButtons() {
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const todoId = btn.getAttribute('data-todo-id');
      
      if (!confirm('Bạn chắc chắn muốn xóa?')) {
        return;
      }
      
      try {
        const response = await fetch(`/dashboard/todos/${todoId}/delete`, {
          method: 'POST'
        });
        
        // Reload page after 300ms
        setTimeout(() => {
          location.reload();
        }, 300);
      } catch (error) {
        console.error('Error:', error);
        alert('Có lỗi xảy ra');
      }
    });
  });
}

/**
 * Initialize all task handlers
 */
function initTasks() {
  initAddTodoForm();
  initCompleteButtons();
  initDeleteButtons();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTasks);
} else {
  initTasks();
}
