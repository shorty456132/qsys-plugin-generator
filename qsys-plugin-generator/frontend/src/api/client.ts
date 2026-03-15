export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const json = await res.json().catch(() => null)
    throw new ApiError(
      (json as { error?: string })?.error || `Server error ${res.status}`,
      res.status
    )
  }
  return res.json()
}

export interface GenerateResponse {
  result: string
  conversation_id: string
}

export interface ReplyResponse {
  result: string
}

export async function generate(formData: FormData): Promise<GenerateResponse> {
  const res = await fetch('/generate', { method: 'POST', body: formData })
  return handleResponse<GenerateResponse>(res)
}

export async function reply(conversationId: string, message: string): Promise<ReplyResponse> {
  const res = await fetch('/reply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, message }),
  })
  return handleResponse<ReplyResponse>(res)
}

export async function downloadPlugin(conversationId: string, pluginName: string): Promise<Blob> {
  const res = await fetch('/download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, plugin_name: pluginName }),
  })
  if (!res.ok) {
    const json = await res.json().catch(() => null)
    throw new ApiError(
      (json as { error?: string })?.error || `Server error ${res.status}`,
      res.status
    )
  }
  return res.blob()
}

export async function completePlugin(conversationId: string, pluginName: string): Promise<Blob> {
  const res = await fetch('/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, plugin_name: pluginName }),
  })
  if (!res.ok) {
    const json = await res.json().catch(() => null)
    throw new ApiError(
      (json as { error?: string })?.error || `Server error ${res.status}`,
      res.status
    )
  }
  return res.blob()
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await fetch('/delete-conversation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId }),
  }).catch(() => {})
}

export function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

export function safeName(name: string): string {
  return name.replace(/[^\w\s-]/g, '').trim().replace(/\s+/g, '-') || 'plugin'
}
