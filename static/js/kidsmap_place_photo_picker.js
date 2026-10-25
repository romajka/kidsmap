/* Route a single visible picker into the existing, validated photo editors. */
(function () {
  function mount() {
    document.querySelectorAll('[data-place-photos-picker]').forEach(function (picker) {
      if (picker.dataset.mounted || !window.DataTransfer) return;
      var form = picker.closest('form');
      if (!form) return;
      var owner = form.querySelector('[data-photo-editor]');
      var gallery = form.querySelector('[data-gallery-root]');
      var main = form.querySelector('#id_photo');
      if (!owner?.kidsmapAddPhotos && (!main || !gallery?.kidsmapAddGalleryPhotos)) return;
      picker.dataset.mounted = '1';
      var mediaSection = picker.closest('[data-place-media-section]');
      if (mediaSection) mediaSection.setAttribute('data-km-photo-unified', '');
      function addSelection(selection) {
        var files = Array.from(selection || []);
        if (!files.length) return;
        if (owner?.kidsmapAddPhotos) owner.kidsmapAddPhotos(files);
        else {
          var saved = form.querySelector('[data-main-photo-root].has-photo');
          if (!saved && !main.files.length) {
            var transfer = new DataTransfer(); transfer.items.add(files.shift());
            main.files = transfer.files;
            main.dispatchEvent(new Event('change', {bubbles:true}));
          }
          if (files.length) gallery.kidsmapAddGalleryPhotos(files);
        }
        picker.value = '';
      }
      picker.addEventListener('change', function () { addSelection(picker.files); });
      var zone = picker.closest('.km-place-photo-picker') || picker.parentElement;
      zone.dataset.kmPhotoDrop = '';
      ['dragenter','dragover'].forEach(function (type) { zone.addEventListener(type,function(event){
        if (Array.from(event.dataTransfer?.types || []).includes('Files')) { event.preventDefault();zone.classList.add('is-dragging'); }
      }); });
      zone.addEventListener('dragleave',function(event){ if (!zone.contains(event.relatedTarget)) zone.classList.remove('is-dragging'); });
      zone.addEventListener('drop',function(event){
        if (!event.dataTransfer?.files?.length) return;
        event.preventDefault();event.stopPropagation();zone.classList.remove('is-dragging');addSelection(event.dataTransfer.files);
      });
      // Keep fallback controls available if the shared handler cannot mount.
      if (owner) owner.querySelectorAll('[data-photo-zone]').forEach(zone => zone.hidden = true);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, {once:true});
  else mount();
})();
