import hashlib
import jinja2
import json
import logging
import markdown
import os
import yaml


DIRECTORY = os.path.dirname(__file__)


logger = logging.getLogger('website')


class InvalidField(ValueError):
    """An invalid value was found in a tool file."""
    def __init__(self, filename, field):
        super(InvalidField, self).__init__(
            "Invalid value for %s in %s" % (field, filename),
        )
        self.filename = filename
        self.field = field


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

    categories = {
        'capture': ('Provenance Capture', {
            'no': ('No', []),
            'yes': ('Yes', []),
            'os': ('OS-Based', []),
            'workflow': ('Workflow-Based', []),
        }),
        'representation': ('Representation', {
            'no': ('No', []),
            'yes': ('Yes', []),
            'descriptive': ('Descriptive-Only', []),
            'executable': ('Executable', []),
        }),
        'replicability': ('Replicability', {
            'no': ('No', []),
            'yes': ('Yes', []),
        }),
        'modifiability': ('Modifiability', {
            'no': ('No', []),
            'yes': ('Yes', []),
        }),
        'portability': ('Portability', {
            'low': ('Low', []),
            'medium': ('Medium', []),
            'high': ('High', []),
            'none': ('None', []),
        }),
        'longevity': ('Longevity', {
            'no': ('No', []),
            'yes': ('Yes', []),
            'archiving': ('Archiving', []),
            'upgrading': ('Upgrading', []),
        }),
        'document-linkage': ('Document Linkage', {
            'no': ('No', []),
            'yes': ('Yes', []),
            'by-ref': ('By Reference', []),
            'inline': ('Inline', []),
        }),
        'sharing': ('Experiment Sharing', {
            'yes': ('Yes', []),
            'no': ('No', []),
            'archival': ('By Reference', []),
            'hosted-execution': ('Inline', []),
        }),
        'os': ('OS Support', {
            'macos': ('macOS', []),
            'windows': ('Windows', []),
            'linux': ('Linux', []),
            'web': ('Web-Based', []),
        }),
    }

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
            def categorize(field, options):
                field_value = meta.get(field)
                try:
                    opt = options[field_value]
                except KeyError:
                    raise InvalidField(tool_file, field_value)
                if opt is None:
                    return
                category, category_value, note = opt
                if note is not None:
                    note = meta.get(note)
                categories[category][1][category_value][1].append(
                    (tool_basename, note),
                )

            categorize('capture', {
                True: ('capture', 'yes', 'capture_note'),
                False: ('capture', 'no', 'capture_note'),
            })
            categorize('capture_os', {
                True: ('capture', 'os', 'capture_note'),
                False: None,
            })
            categorize('capture_workflow', {
                True: ('capture', 'workflow', 'capture_note'),
                False: None,
            })
            # TODO: capture_code, capture_data?
            categorize('representation', {
                True: ('representation', 'yes', 'representation_note'),
                False: ('representation', 'no', 'representation_note'),
            })
            categorize('representation_descriptive_only', {
                True: ('representation', 'descriptive', 'representation_note'),
                False: None,
            })
            categorize('representation_executable', {
                True: ('representation', 'executable', 'representation_note'),
                False: None,
            })
            categorize('replicability', {
                True: ('replicability', 'yes', 'replicability_note'),
                False: ('replicability', 'no', 'replicability_note'),
            })
            categorize('modifiability', {
                True: ('modifiability', 'yes', 'modifiability_note'),
                False: ('modifiability', 'no', 'modifiability_note'),
            })
            categorize('portability', {
                'LOW': ('portability', 'low', 'portability_note'),
                'MEDIUM': ('portability', 'medium', 'portability_note'),
                'HIGH': ('portability', 'high', 'portability_note'),
                'NONE': ('portability', 'none', 'portability_note'),
            })
            categorize('longevity', {
                True: ('longevity', 'yes', None),
                False: ('longevity', 'no', None),
            })
            categorize('longevity_archiving', {
                True: ('longevity', 'archiving', None),
                False: None,
            })
            categorize('longevity_upgrading', {
                True: ('longevity', 'upgrading', None),
                False: None,
            })
            categorize('document_linkage', {
                True: ('document-linkage', 'yes', None),
                False: ('document-linkage', 'no', None),
            })
            categorize('document_linkage_by_reference', {
                True: ('document-linkage', 'by-ref', None),
                False: None,
            })
            categorize('document_linkage_inline', {
                True: ('document-linkage', 'inline', None),
                False: None,
            })
            categorize('experiment_sharing', {
                True: ('sharing', 'yes', None),
                False: ('sharing', 'no', None),
            })
            categorize('experiment_sharing_archival', {
                True: ('sharing', 'archival', None),
                False: None,
            })
            categorize('experiment_sharing_archival', {
                True: ('sharing', 'hosted-execution', None),
                False: None,
            })
            categorize('supports_linux', {
                True: ('os', 'linux', 'supports_note'),
                False: None,
            })
            categorize('supports_osx', {
                True: ('os', 'macos', 'supports_note'),
                False: None,
            })
            categorize('supports_web_based', {
                True: ('os', 'web', 'supports_note'),
                False: None,
            })
            categorize('supports_windows', {
                True: ('os', 'windows', 'supports_note'),
                False: None,
            })

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
    for category, (cat_name, values) in categories.items():
        for category_value, (catval_name, tools) in values.items():
            shortname = '{0}-{1}.html'.format(category, category_value)
            with open(os.path.join(output_dir, shortname), 'w') as f_out:
                f_out.write(category_template.render(
                    category=cat_name,
                    category_value=catval_name,
                    tools=sorted(tools, key=lambda p: p[0].lower()),
                ))

    # Generate index
    logger.info("Creating index page")
    index_template = template_env.get_template('index.html')
    with open(os.path.join(output_dir, 'index.html'), 'w') as f_out:
        f_out.write(index_template.render(
            categories=[
                (
                    category,
                    name,
                    [(value, catval_name) for value, (catval_name, tools) in values.items()],
                )
                for category, (name, values) in categories.items()
            ],
        ))

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
