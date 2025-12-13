import { useCallback, useState } from 'react'
import { Upload, File, X, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FilePickerProps {
    onFileSelect: (file: File) => void
    accept?: string
    isUploading?: boolean
}

export default function FilePicker({ onFileSelect, accept = '.pdf,.png,.jpg,.jpeg,.tiff', isUploading }: FilePickerProps) {
    const [dragOver, setDragOver] = useState(false)
    const [selectedFile, setSelectedFile] = useState<File | null>(null)

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setDragOver(true)
    }, [])

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setDragOver(false)
    }, [])

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        if (file) {
            setSelectedFile(file)
            onFileSelect(file)
        }
    }, [onFileSelect])

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (file) {
            setSelectedFile(file)
            onFileSelect(file)
        }
    }

    const clearFile = () => {
        setSelectedFile(null)
    }

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    }

    return (
        <div className="w-full">
            {!selectedFile ? (
                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                        'border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer',
                        dragOver
                            ? 'border-primary bg-primary/5'
                            : 'border-border hover:border-primary/50 hover:bg-muted/50'
                    )}
                >
                    <input
                        type="file"
                        accept={accept}
                        onChange={handleFileChange}
                        className="hidden"
                        id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                        <div className="flex flex-col items-center gap-4">
                            <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                                <Upload className="w-8 h-8 text-primary" />
                            </div>
                            <div>
                                <p className="text-lg font-medium">Drop your file here or click to browse</p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Supports PDF, PNG, JPG, TIFF (max 50MB)
                                </p>
                            </div>
                        </div>
                    </label>
                </div>
            ) : (
                <div className="border rounded-xl p-4">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center">
                            <File className="w-6 h-6 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{selectedFile.name}</p>
                            <p className="text-sm text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
                        </div>
                        {isUploading ? (
                            <Loader2 className="w-5 h-5 text-primary animate-spin" />
                        ) : (
                            <button
                                onClick={clearFile}
                                className="p-2 hover:bg-muted rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-muted-foreground" />
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
