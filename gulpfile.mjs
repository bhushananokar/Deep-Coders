import gulp from 'gulp';
import open from 'gulp-open';

// Task to open the browser
gulp.task('open-app', function(){
  gulp.src('index.html')
  .pipe(open());
});

// Add a build task for Netlify
gulp.task('build', function(done){
  // This task doesn't do anything special since your project might just need
  // to serve static files without a build process
  console.log('Build completed');
  done();
});
