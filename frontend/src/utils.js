export function roleLabel(role) {
  if (role === 'admin') return 'Admin'
  if (role === 'clerk') return 'Clerk'
  if (role === 'student') return 'Student'
  return role || ''
}

export function hostelLabel(value) {
  if (value === 'boys_hostel') return 'Boys Hostel'
  if (value === 'girls_hostel') return 'Girls Hostel'
  return value || '-'
}

export function statusLabel(value) {
  if (!value) return '-'
  return value.replaceAll('_', ' ').replace(/\b\w/g, (m) => m.toUpperCase())
}

export function yearLabel(value) {
  if (value === 'year_1') return 'Year 1'
  if (value === 'year_2') return 'Year 2'
  if (value === 'year_3') return 'Year 3'
  return value || '-'
}

export function fileTypeLabel(value) {
  if (!value) return '-'
  return value.replaceAll('_', ' ').replace(/\b\w/g, (m) => m.toUpperCase())
}

export function formatDate(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

export function downloadCsv(filename, rows) {
  const csv = rows.map((row) => row.map(csvCell).join(',')).join('\r\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function csvCell(value) {
  const text = String(value ?? '')
  return `"${text.replaceAll('"', '""')}"`
}

export function parseCsvText(text) {
  const lines = text.split(/\r?\n/).filter((line) => line.trim())
  if (!lines.length) return []
  const headers = splitCsvLine(lines[0]).map((h) => h.trim())
  return lines.slice(1).map((line) => {
    const values = splitCsvLine(line)
    const row = {}
    headers.forEach((header, index) => {
      row[header] = values[index] ?? ''
    })
    return row
  })
}

function splitCsvLine(line) {
  const out = []
  let cur = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    const next = line[i + 1]
    if (ch === '"') {
      if (inQuotes && next === '"') {
        cur += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
    } else if (ch === ',' && !inQuotes) {
      out.push(cur)
      cur = ''
    } else {
      cur += ch
    }
  }
  out.push(cur)
  return out
}