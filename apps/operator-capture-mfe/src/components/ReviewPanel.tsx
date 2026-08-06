import { Box, Button, Card, CardContent, Stack, Typography } from '@mui/material'
import CloudUploadIcon from '@mui/icons-material/CloudUpload'
import ReplayIcon from '@mui/icons-material/Replay'
import { useApp } from './appContext'
import type { RecorderResult } from '../recorder/useRecorder'

interface ReviewPanelProps {
  result: RecorderResult
  onDiscard: () => void
  onConfirm: () => void
}

function formatDuration(seconds: number): string {
  const total = Math.round(seconds)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export function ReviewPanel({ result, onDiscard, onConfirm }: ReviewPanelProps) {
  const { t } = useApp()
  return (
    <Card>
      <CardContent>
        <Stack spacing={2.5}>
          <Typography variant="h2">{t('review.title')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('review.hint')}
          </Typography>

          <Box>
            <Typography variant="caption" color="text.secondary">
              {t('review.duration')}: {formatDuration(result.durationSeconds)}
            </Typography>
            {/* Local playback of the not-yet-uploaded recording. */}
            <Box
              component="audio"
              controls
              src={result.url}
              aria-label={t('review.title')}
              sx={{ width: '100%', mt: 1 }}
            />
          </Box>

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <Button variant="outlined" size="large" fullWidth onClick={onDiscard} startIcon={<ReplayIcon />}>
              {t('review.discard')}
            </Button>
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={onConfirm}
              startIcon={<CloudUploadIcon />}
            >
              {t('review.confirm')}
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}
