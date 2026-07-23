<?php

declare(strict_types=1);

final class TemplateRenderer
{
    private string $templateDir;

    /** @var array<string, string> */
    private array $vars;

    public function __construct(string $templateDir, array $vars = [])
    {
        $this->templateDir = rtrim($templateDir, '/');
        $this->vars = $vars;
    }

    public function render(string $template): string
    {
        $content = $this->load($template);

        if (preg_match('/\{%\s*extends\s+"([^"]+)"\s*%\}/', $content, $match) === 1) {
            $blocks = $this->extractBlocks($content);
            $html = $this->applyBlocks($this->load($match[1]), $blocks);
        } else {
            $html = $content;
        }

        return $this->process($html);
    }

    private function load(string $template): string
    {
        $path = $this->templateDir . '/' . ltrim($template, '/');
        if (!is_readable($path)) {
            throw new RuntimeException("Template not found: {$template}");
        }

        $content = file_get_contents($path);
        if ($content === false) {
            throw new RuntimeException("Template not readable: {$template}");
        }

        return $content;
    }

    /** @return array<string, string> */
    private function extractBlocks(string $content): array
    {
        $blocks = [];
        if (preg_match_all(
            '/\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}/s',
            $content,
            $matches,
            PREG_SET_ORDER
        ) !== false) {
            foreach ($matches as $match) {
                $blocks[$match[1]] = $match[2];
            }
        }

        return $blocks;
    }

    /** @param array<string, string> $blocks */
    private function applyBlocks(string $parent, array $blocks): string
    {
        $result = preg_replace_callback(
            '/\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}/s',
            static function (array $match) use ($blocks): string {
                $name = $match[1];
                return array_key_exists($name, $blocks) ? $blocks[$name] : $match[2];
            },
            $parent
        );

        return $result ?? $parent;
    }

    private function process(string $html): string
    {
        $previous = null;
        while ($previous !== $html) {
            $previous = $html;
            $html = preg_replace_callback(
                '/\{%\s*include\s+"([^"]+)"\s*%\}/',
                fn (array $match): string => $this->renderPartial($match[1]),
                $html
            ) ?? $html;
        }

        $html = preg_replace_callback(
            '/\{\{\s*(\w+)\s*\}\}/',
            function (array $match): string {
                $key = $match[1];
                if (!array_key_exists($key, $this->vars)) {
                    return '';
                }

                return htmlspecialchars((string) $this->vars[$key], ENT_QUOTES, 'UTF-8');
            },
            $html
        ) ?? $html;

        return preg_replace('/\{%[^%]+%\}/', '', $html) ?? $html;
    }

    private function renderPartial(string $template): string
    {
        $content = $this->load($template);
        if (preg_match('/\{%\s*extends\s+"([^"]+)"\s*%\}/', $content) === 1) {
            throw new RuntimeException("Nested extends not supported in include: {$template}");
        }

        return $this->process($content);
    }
}
