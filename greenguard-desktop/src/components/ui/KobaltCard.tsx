import { ReactNode } from 'react';

interface KobaltCardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: ReactNode;
    className?: string;
    hover?: boolean;
    padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const KobaltCard = ({
    children,
    className = "",
    hover = true,
    padding = 'md',
    ...props
}: KobaltCardProps) => {
    const paddings = {
        none: "",
        sm: "p-4",
        md: "p-6",
        lg: "p-8"
    };

    return (
        <div
            className={`
                bg-white 
                rounded-2xl 
                border border-kobalt-border
                shadow-sm hover:shadow-md
                ${hover ? 'hover:-translate-y-0.5' : ''}
                transition-all duration-300
                ${paddings[padding]}
                ${className}
            `}
            {...props}
        >
            {children}
        </div>
    );
};
