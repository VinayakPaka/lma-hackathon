import { InputHTMLAttributes, forwardRef } from 'react';

interface KobaltInputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    icon?: React.ReactNode;
}

export const KobaltInput = forwardRef<HTMLInputElement, KobaltInputProps>(
    ({ label, error, icon, className = "", ...props }, ref) => {
        return (
            <div className="w-full space-y-1.5">
                {label && (
                    <label className="block text-xs font-semibold text-kobalt-black/70 uppercase tracking-wider ml-1">
                        {label}
                    </label>
                )}
                <div className="relative">
                    {icon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                            {icon}
                        </div>
                    )}
                    <input
                        ref={ref}
                        className={`
                            w-full 
                            bg-kobalt-gray/50 
                            border border-transparent 
                            rounded-xl 
                            px-4 py-3 
                            text-kobalt-black 
                            placeholder:text-gray-400
                            transition-all duration-200
                            focus:bg-white 
                            focus:border-kobalt-blue/30 
                            focus:ring-4 focus:ring-kobalt-blue/10 
                            focus:outline-none 
                            disabled:opacity-50 disabled:cursor-not-allowed
                            ${icon ? 'pl-10' : ''}
                            ${error ? 'bg-red-50 border-red-200 focus:border-red-500 focus:ring-red-100' : ''}
                            ${className}
                        `}
                        {...props}
                    />
                </div>
                {error && (
                    <p className="text-xs text-red-500 font-medium ml-1 animate-fadeIn">
                        {error}
                    </p>
                )}
            </div>
        );
    }
);

KobaltInput.displayName = "KobaltInput";
