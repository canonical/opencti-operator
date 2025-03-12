# How to redeploy the OpenCTI charm

Both the OpenCTI charm and the OpenCTI connector are stateless charms, so you 
can redeploy the OpenCTI charm at any time using `juju refresh`.

However, one thing to keep in mind is that the newly deployed charm must use the
same Juju application name as the previous OpenCTI charm. This is because the
OpenCTI charm uses the Juju application name as the OpenSearch index prefix. 
Using the same Juju application name ensures that the new OpenCTI charm inherits the old data created by
the previous charm.
