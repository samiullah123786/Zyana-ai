import * as chokidar from 'chokidar';
import * as path from 'path';
import { ApiClient } from './apiClient';
import Store from 'electron-store';

const store = new Store();

export class FileWatcher {
  private watchers: chokidar.FSWatcher[] = [];
  private apiClient: ApiClient;
  private watchFolders: string[];

  constructor(watchFolders: string[], apiUrl: string, authToken: string) {
    this.watchFolders = watchFolders;
    this.apiClient = new ApiClient(apiUrl, authToken);
  }

  start() {
    console.log('Starting file watchers...');
    
    this.watchFolders.forEach(folder => {
      const watcher = chokidar.watch(folder, {
        ignored: /(^|[\/\\])\../, // ignore dotfiles
        persistent: true,
        ignoreInitial: true,
      });

      watcher
        .on('add', (filePath) => this.handleNewFile(filePath))
        .on('error', (error) => console.error(`Watcher error: ${error}`));

      this.watchers.push(watcher);
      console.log(`Watching folder: ${folder}`);
    });
  }

  stop() {
    console.log('Stopping file watchers...');
    this.watchers.forEach(watcher => watcher.close());
    this.watchers = [];
  }

  private async handleNewFile(filePath: string) {
    const ext = path.extname(filePath).toLowerCase();
    const videoExtensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm'];

    if (!videoExtensions.includes(ext)) {
      return;
    }

    console.log(`New video file detected: ${filePath}`);
    this.addLog('info', `New video file detected: ${path.basename(filePath)}`);

    try {
      // Extract metadata
      const metadata = {
        fileName: path.basename(filePath),
        filePath: filePath,
        extension: ext,
        detectedAt: new Date().toISOString(),
      };

      // Submit job to backend
      const result = await this.apiClient.submitVideoJob(metadata);

      if (result.success) {
        this.addLog('success', `Job created for: ${metadata.fileName}`);
      } else {
        this.addLog('error', `Failed to create job: ${result.message}`);
      }
    } catch (error) {
      console.error('Error handling new file:', error);
      this.addLog('error', `Error processing file: ${error}`);
    }
  }

  private addLog(level: string, message: string) {
    const logs = store.get('logs', []) as any[];
    logs.unshift({
      level,
      message,
      timestamp: new Date().toISOString(),
    });

    // Keep only last 100 logs
    if (logs.length > 100) {
      logs.pop();
    }

    store.set('logs', logs);
  }
}

