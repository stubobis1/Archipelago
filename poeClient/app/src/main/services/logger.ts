import log from 'electron-log'
import { app } from 'electron'
import * as path from 'path'

log.transports.file.resolvePathFn = () =>
  path.join(app.getPath('logs'), 'main.log')
log.transports.file.level = 'debug'
log.transports.console.level = 'debug'
log.transports.file.maxSize = 5 * 1024 * 1024

export const logger = log

export function initLogger(): void {
  log.info('=== PoE Archipelago Client starting ===')
  log.info('Log file:', log.transports.file.getFile().path)
  log.errorHandler.startCatching({ showDialog: false })
}
