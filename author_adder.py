# Author: Amir Sarabadani
# License: MIT
import pywikibot
from pywikibot import Bot, pagegenerators
import codecs
import json
import re

summary = 'Bot: Prova'
site = pywikibot.Site('it', 'wikisource')


def get_authors_list():
    authors = []
    category = pywikibot.Category(site, 'Categoria:Autori')
    gen = pagegenerators.CategorizedPageGenerator(category)
    for page in pagegenerators.PreloadingGenerator(gen):
        authors.append(page.title(withNamespace=False))
    return authors


def load_cache():
    with codecs.open('authors.txt', 'r', 'utf-8') as f:
        return json.load(f)


def write_cache(data=None):
    if not data:
        print('Loading names of authors...')
        data = get_authors_list()
    with codecs.open('authors.txt', 'w', 'utf-8') as f:
        json.dump(data, f)


class AuthorBot(Bot):
    """AuthorBot"""
    def __init__(self, gen, site, no_cache, last_name, auto):
        super(AuthorBot, self).__init__()
        self._site = site
        self.generator = gen
        if no_cache:
            write_cache()
        self.authors = {}
        if not last_name:
            for author in load_cache():
                self.authors[author] = author
        else:
            for author in load_cache():
                temp = author.split(' (')[0]
                temp = re.split(r' I(?:\W|I|V|X|M|$)', temp)[0]
                temp = temp.split(' ')[-1]
                self.authors[temp] = author
        self.auto = auto

    def treat(self, page):
        self.current_page = page
        try:
            text = page.get()
            for author in self.authors:
                if re.search(r'(\b%s\b)' % re.escape(author), text):
                    if self.authors[author] == author:
                        text = text.replace(
                            author, u'{{AutoreCitato|%s}}' % author)
                    else:
                        text = text.replace(
                            author, u'{{AutoreCitato|%s|%s}}'
                                    % (self.authors[author], author))
            if page.text != text:
                if self.auto:
                    page.text = text
                    page.save(summary)
                else:
                    pywikibot.showDiff(page.text, text)
                    choice = pywikibot.input('Agree? [Y]es, [N]o')
                    if choice.lower() == 'y':
                        page.text = text
                        page.save(summary)
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist?!"
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked?!" % page.title(asLink=True))


def main(*args):
    no_cache = False
    last_name = False
    auto = False
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        elif arg == '--nocache':
            no_cache = True
        elif arg == '--last':
            last_name = True
        elif arg == '--auto':
            auto = True
    gen = genFactory.getCombinedGenerator()
    if not gen:
        pywikibot.error('You must define something')
    preloading_gen = pagegenerators.PreloadingGenerator(gen)
    bot = AuthorBot(preloading_gen, site, no_cache, last_name, auto)
    site.login()
    bot.run()


if __name__ == "__main__":
        main()
