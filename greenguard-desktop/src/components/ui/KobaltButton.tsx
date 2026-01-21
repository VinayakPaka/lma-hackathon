

interface KobaltButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'outline';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

export const KobaltButton = ({
    children,
    variant = 'primary',
    size = 'md',
    isLoading,
    className = "",
    ...props
}: KobaltButtonProps) => {
    const baseStyles = "inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";

    const variants = {
        primary: "bg-kobalt-blue text-white hover:bg-blue-700 shadow-sm hover:shadow-md border border-transparent focus:ring-kobalt-blue",
        secondary: "bg-white text-kobalt-black hover:bg-gray-50 shadow-sm hover:shadow-md border border-gray-100 focus:ring-gray-200",
        ghost: "bg-transparent text-kobalt-black hover:bg-kobalt-gray/50 hover:text-kobalt-blue",
        outline: "bg-transparent border border-kobalt-border text-kobalt-black hover:bg-kobalt-gray/30"
    };

    const sizes = {
        sm: "text-xs px-3 py-1.5 rounded-lg",
        md: "text-sm px-5 py-2.5 rounded-xl",
        lg: "text-base px-6 py-3 rounded-xl"
    };

    return (
        <button
            className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
            disabled={isLoading || props.disabled}
            {...props}
        >
            {isLoading && (
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            )}
            {children}
        </button>
    );
};
