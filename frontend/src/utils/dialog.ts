function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/\n/g, '<br />')
}

interface DialogOptions {
  message: string
  defaultValue?: string
  confirmText?: string
  cancelText?: string
  showCancel?: boolean
  showInput?: boolean
}

function ensureDialogStyles() {
  if (typeof document === 'undefined') return
  if (document.getElementById('custom-dialog-styles')) return

  const style = document.createElement('style')
  style.id = 'custom-dialog-styles'
  style.textContent = `
    .custom-dialog-overlay {
      position: fixed;
      inset: 0;
      background: rgba(15, 23, 42, 0.45);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 16px;
      z-index: 99999;
      backdrop-filter: blur(4px);
    }
    .custom-dialog-box {
      width: min(92vw, 420px);
      background: rgba(255, 255, 255, 0.98);
      border-radius: 18px;
      box-shadow: 0 18px 48px rgba(15, 23, 42, 0.18);
      overflow: hidden;
      animation: customDialogIn 0.18s ease-out;
    }
    .custom-dialog-header {
      padding: 18px 22px 10px;
      font-size: 18px;
      font-weight: 700;
      color: #1677ff;
      text-align: center;
    }
    .custom-dialog-body {
      padding: 8px 22px 20px;
      color: #1f2937;
      font-size: 14px;
      line-height: 1.7;
      text-align: center;
      word-break: break-word;
    }
    .custom-dialog-input {
      width: 100%;
      margin-top: 14px;
      padding: 12px 14px;
      border: 1px solid rgba(148, 163, 184, 0.45);
      border-radius: 12px;
      outline: none;
      font-size: 14px;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .custom-dialog-input:focus {
      border-color: #1677ff;
      box-shadow: 0 0 0 3px rgba(22, 119, 255, 0.12);
    }
    .custom-dialog-footer {
      display: flex;
      gap: 12px;
      justify-content: center;
      padding: 0 22px 22px;
    }
    .custom-dialog-btn {
      min-width: 104px;
      padding: 10px 16px;
      border-radius: 12px;
      border: none;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease, opacity 0.2s ease, box-shadow 0.2s ease;
    }
    .custom-dialog-btn:hover {
      transform: translateY(-1px);
    }
    .custom-dialog-btn.primary {
      background: linear-gradient(135deg, #1677ff 0%, #0958d9 100%);
      color: #fff;
      box-shadow: 0 10px 20px rgba(22, 119, 255, 0.22);
    }
    .custom-dialog-btn.secondary {
      background: rgba(148, 163, 184, 0.15);
      color: #334155;
    }
    @keyframes customDialogIn {
      from {
        opacity: 0;
        transform: translateY(10px) scale(0.98);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }
  `
  document.head.appendChild(style)
}

function openDialog(options: DialogOptions): Promise<boolean | string | null> {
  if (typeof document === 'undefined') {
    return Promise.resolve(options.showInput ? options.defaultValue ?? '' : true)
  }

  ensureDialogStyles()

  return new Promise((resolve) => {
    const overlay = document.createElement('div')
    overlay.className = 'custom-dialog-overlay'
    overlay.innerHTML = `
      <div class="custom-dialog-box" role="dialog" aria-modal="true" aria-label="温馨提示">
        <div class="custom-dialog-header">温馨提示：</div>
        <div class="custom-dialog-body">
          <div>${escapeHtml(options.message)}</div>
          ${options.showInput ? `<input class="custom-dialog-input" value="${escapeHtml(options.defaultValue ?? '')}" />` : ''}
        </div>
        <div class="custom-dialog-footer">
          ${options.showCancel ? `<button class="custom-dialog-btn secondary" data-action="cancel">${escapeHtml(options.cancelText ?? '取消')}</button>` : ''}
          <button class="custom-dialog-btn primary" data-action="confirm">${escapeHtml(options.confirmText ?? '确定')}</button>
        </div>
      </div>
    `

    const cleanup = () => {
      document.removeEventListener('keydown', handleKeydown)
      overlay.remove()
    }

    const confirm = () => {
      const input = overlay.querySelector<HTMLInputElement>('.custom-dialog-input')
      const value = options.showInput ? (input?.value ?? '') : true
      cleanup()
      resolve(value)
    }

    const cancel = () => {
      cleanup()
      resolve(options.showInput ? null : false)
    }

    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && options.showCancel) {
        cancel()
      }
      if (event.key === 'Enter') {
        event.preventDefault()
        confirm()
      }
    }

    document.addEventListener('keydown', handleKeydown)
    overlay.addEventListener('click', (event) => {
      const target = event.target as HTMLElement
      const action = target.getAttribute('data-action')
      if (action === 'confirm') confirm()
      if (action === 'cancel') cancel()
    })

    document.body.appendChild(overlay)
    const input = overlay.querySelector<HTMLInputElement>('.custom-dialog-input')
    if (input) {
      window.setTimeout(() => {
        input.focus()
        input.select()
      }, 0)
    }
  })
}

export function showAlert(message: string) {
  return openDialog({ message, confirmText: '我知道了' }).then(() => undefined)
}

export function showConfirm(message: string) {
  return openDialog({
    message,
    confirmText: '确定',
    cancelText: '取消',
    showCancel: true,
  }).then((result) => Boolean(result))
}

export function showPrompt(message: string, defaultValue = '') {
  return openDialog({
    message,
    defaultValue,
    confirmText: '确定',
    cancelText: '取消',
    showCancel: true,
    showInput: true,
  }).then((result) => (typeof result === 'string' ? result : null))
}
