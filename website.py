import jinja2
import logging
import markdown
import os
import yaml


DIRECTORY = os.path.dirname(__file__)


logger = logging.getLogger('website')


def main():
    logging.basicConfig(level=logging.INFO)

    # Initialize directories
    tools_dir = os.path.join(DIRECTORY, 'tools')
    output_dir = os.path.join(DIRECTORY, '_website')
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    # Load templates
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(['templates']),
        autoescape=jinja2.select_autoescape(['html']),
    )

    # Categories
    capture = []
    sharing = []

    # Process each tool file
    tool_template = template_env.get_template('tool.html')
    for tool_file in os.listdir(tools_dir):
        logger.info("Processing %s", tool_file)
        tool_basename = os.path.splitext(tool_file)[0]
        tool_file = os.path.join(tools_dir, tool_file)
        if not tool_file.endswith('.txt'):
            continue
        tool_output = os.path.join(output_dir, '%s.html' % tool_basename)

        with open(tool_file) as f_in:
            # Read header
            header = []
            for line in f_in:
                if line.startswith('---'):
                    break
                header.append(line)
            header = ''.join(header)

            # Load as YAML
            meta = yaml.safe_load(header)

            # Read content
            content = []
            for line in f_in:
                if content or line:
                    content.append(line)
            content = ''.join(content)

            # Render markdown
            content = markdown.markdown(content)

            # Open output
            with open(tool_output, 'w') as f_out:
                f_out.write(tool_template.render(
                    content=jinja2.Markup(content),
                    meta=meta,
                ))

            # Add to categories
            if meta.get('capture'):
                capture.append((tool_basename, meta.get('capture_note')))
            if meta.get('experiment_sharing'):
                sharing.append((tool_basename, None))

    # Generate category pages
    category_template = template_env.get_template('category.html')
    with open(os.path.join(output_dir, 'capture.html'), 'w') as f_out:
        f_out.write(category_template.render(
            category='capture',
            tools=capture,
        ))
    with open(os.path.join(output_dir, 'sharing.html'), 'w') as f_out:
        f_out.write(category_template.render(
            category='sharing',
            tools=sharing,
        ))

    # Generate index
    index_template = template_env.get_template('index.html')
    with open(os.path.join(output_dir, 'index.html'), 'w') as f_out:
        f_out.write(index_template.render())


if __name__ == '__main__':
    main()
