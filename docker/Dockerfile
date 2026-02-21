FROM nginx:alpine

# Remove default nginx content
RUN rm -rf /usr/share/nginx/html/*

# Copy dashboard files
COPY index.html /usr/share/nginx/html/index.html

# Optional: copy additional assets if added later
# COPY css/ /usr/share/nginx/html/css/
# COPY js/ /usr/share/nginx/html/js/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
