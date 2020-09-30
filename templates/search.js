var searchIndex = undefined;

(function() {
  var req = new XMLHttpRequest();
  req.responseType = 'json';
  req.open('GET', '{{ search_index_file }}', true);
  req.onload = function() {
    console.log('Search index loaded');
    searchIndex = req.response;
  };
  req.send();
})();

function search(words) {
  if(!searchIndex || !words.length) {
    return undefined;
  }

  // Split words
  words = words.split(/[+, ]+/);
  if(!words || !words.length) {
    return undefined;
  }

  // Get result for first word
  var word = words[0].toLowerCase()
  var matches = searchIndex[word];
  if(!matches) {
    return [];
  }
  matches = matches.slice();

  // Remove results that don't match the other words
  for(var i = 1; i < words.length; ++i) {
    var word = words[i].toLowerCase();
    var hits = new Set(searchIndex[word]);
    for(var j = 0; j < matches.length;) {
      if(hits.has(matches[j])) {
        ++j;
      } else {
        matches.splice(j, 1);
      }
    }
  }

  return matches;
}
