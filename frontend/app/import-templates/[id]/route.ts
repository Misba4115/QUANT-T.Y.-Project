import { IMPORT_TEMPLATES } from '@/lib/import-templates';

export async function GET(
    _request: Request,
    context: { params: Promise<{ id: string }> },
) {
    const { id } = await context.params;
    const template = IMPORT_TEMPLATES.find((item) => item.id === id);
    if (!template) {
        return Response.json({ detail: 'Import template not found' }, { status: 404 });
    }

    return new Response(template.csv, {
        headers: {
            'Content-Type': template.contentType ?? 'text/csv; charset=utf-8',
            'Content-Disposition': `attachment; filename="${template.filename}"`,
            'Cache-Control': 'public, max-age=3600',
        },
    });
}
