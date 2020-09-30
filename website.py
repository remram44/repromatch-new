import hashlib
import jinja2
import json
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

    # Search index
    search_index = {}

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
                    basename=tool_basename,
                ))

            # Add to categories
            if meta.get('capture'):
                capture.append((tool_basename, meta.get('capture_note')))
            if meta.get('experiment_sharing'):
                sharing.append((tool_basename, None))

            # Add to search index
            keywords = {tool_basename}
            if 'name' in meta:
                keywords.add(meta['name'])
                for word in meta['name'].split():
                    keywords.add(word)
            keywords = {keyword.lower() for keyword in keywords}
            for keyword in keywords:
                search_index.setdefault(keyword, []).append(tool_basename)

    # Generate category pages
    logger.info("Creating category pages")
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
    logger.info("Creating index page")
    index_template = template_env.get_template('index.html')
    with open(os.path.join(output_dir, 'index.html'), 'w') as f_out:
        f_out.write(index_template.render())

    # Remove previous search indexes
    logger.info("Generating search index")
    for name in os.listdir(output_dir):
        if name.startswith('search-index') and name.endswith('.js'):
            os.remove(os.path.join(output_dir, name))

    # Generate search index
    search_index = sorted(
        (keyword, sorted(tools))
        for keyword, tools in search_index.items()
    )
    with open(os.path.join(output_dir, 'search-index.js'), 'w') as f_out:
        f_out = HashedFile(f_out)
        f_out.write('{')
        first = True
        for keyword, tools in search_index:
            if not first:
                f_out.write(',')
            else:
                first = False
            f_out.write('%s: %s' % (json.dumps(keyword), json.dumps(tools)))
        f_out.write('}')
    search_index_file = 'search-index.%s.js' % f_out.hexdigest()[:8]
    os.rename(
        os.path.join(output_dir, 'search-index.js'),
        os.path.join(output_dir, search_index_file),
    )

    # Copy search script
    search_template = template_env.get_template('search.js')
    with open(os.path.join(output_dir, 'search.js'), 'w') as f_out:
        f_out.write(search_template.render(
            search_index_file=search_index_file,
        ))


class HashedFile(object):
    def __init__(self, fp):
        self._fp = fp
        self._hash = hashlib.sha1()

    def write(self, buf):
        self._hash.update(buf.encode('utf-8'))
        return self._fp.write(buf)

    def hexdigest(self):
        return self._hash.hexdigest()


if __name__ == '__main__':
    main()
